"""
Phase 4 - Step 2: LangGraph 기본 에이전트
State → Agent → Tools → Agent → ... → END 흐름
실행: python phase4/02_langgraph_basic.py
"""
import json
import operator
from typing import Annotated
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv

load_dotenv()

# ── 1. 도구 정의 (@tool 데코레이터) ──────────────────────────────────
@tool
def get_device_status(device_id: str) -> str:
    """스마트홈 기기의 현재 상태를 조회합니다."""
    db = {
        "device_003": json.dumps({"status": "offline", "type": "거실 에어컨", "last_seen": "52분 전"}, ensure_ascii=False),
        "device_001": json.dumps({"status": "online",  "type": "현관 도어락", "signal": -62}, ensure_ascii=False),
    }
    return db.get(device_id, '{"status": "not_found"}')

@tool
def get_error_logs(device_id: str) -> str:
    """기기의 최근 에러 로그를 조회합니다."""
    if device_id == "device_003":
        return "CONNECTION_LOST(-85dBm) × 3회, TIMEOUT(-95dBm) × 2회 — 신호 강도 지속 약화"
    return "에러 없음"

@tool
def create_jira_ticket(summary: str, priority: str = "High") -> str:
    """장애 Jira 티켓을 생성합니다."""
    print(f"  [Jira] {priority} | {summary}")
    return f"SMART-{hash(summary) % 9999:04d} 생성 완료"

@tool
def send_slack_alert(channel: str, message: str) -> str:
    """Slack 채널에 알림을 전송합니다."""
    print(f"  [Slack] #{channel}: {message[:60]}")
    return "전송 완료"

tools = [get_device_status, get_error_logs, create_jira_ticket, send_slack_alert]

# ── 2. 상태(State) 정의 ───────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # 메시지 누적

# ── 3. 노드 함수 ──────────────────────────────────────────────────────
llm = ChatAnthropic(model="claude-opus-4-7", max_tokens=2048).bind_tools(tools)

SYSTEM = SystemMessage(content="""스마트홈 운영 자동화 AI입니다.
오프라인 기기 발견 시: 에러 로그 확인 → Jira 티켓(High) → Slack #smarthome-ops 알림
온라인 기기: 상태만 보고""")

def agent_node(state: AgentState) -> AgentState:
    response = llm.invoke([SYSTEM] + state["messages"])
    return {"messages": [response]}

# ── 4. 그래프 구성 ─────────────────────────────────────────────────────
tool_node = ToolNode(tools)

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tools_condition)  # 도구 필요 → tools, 아니면 END
graph.add_edge("tools", "agent")

app = graph.compile()

# ── 5. 실행 ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("LangGraph 에이전트 실행\n" + "=" * 50)

    result = app.invoke({
        "messages": [HumanMessage(content=
            "device_001이랑 device_003 상태 확인하고 문제 있는 거 자동으로 처리해줘"
        )]
    })

    print("\n최종 답변:")
    print(result["messages"][-1].content)
