"""
Phase 4 - 실습 프로젝트: VOC 자동화 에이전트
고객 문의 → 분류 → 관련 로그 조회 → 답변 초안 → 담당자 전달

직방 JD 핵심 요구사항:
"VOC 자동 조사, 장애 탐지, CS 자동 대응"

실행: python phase4/04_voc_agent.py
"""
import operator
import json
from typing import Annotated
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv

load_dotenv()
llm = ChatAnthropic(model="claude-opus-4-7", max_tokens=2048)

# ── 도구 ──────────────────────────────────────────────────────────────
@tool
def classify_voc(inquiry: str) -> str:
    """고객 문의를 카테고리와 심각도로 분류합니다."""
    # 실제로는 LLM 또는 분류 모델 사용
    keywords = {
        "배터리": ("배터리_부족", "중"),
        "오프라인": ("연결_오류", "높"),
        "안 켜": ("제어_오류", "중"),
        "자동": ("자동화_오류", "낮"),
        "앱":  ("앱_오류",   "중"),
    }
    for kw, (cat, sev) in keywords.items():
        if kw in inquiry:
            return json.dumps({"category": cat, "severity": sev}, ensure_ascii=False)
    return json.dumps({"category": "기타", "severity": "낮"}, ensure_ascii=False)

@tool
def search_device_logs(category: str) -> str:
    """카테고리에 맞는 관련 기기 로그를 조회합니다."""
    logs = {
        "연결_오류":  "device_003: CONNECTION_LOST × 3, signal -85→-95dBm (최근 1시간)",
        "제어_오류":  "device_002: API_TIMEOUT × 1 (10:45), 이후 정상",
        "배터리_부족": "device_001: BATTERY_LOW (잔량 12%) 경고 발생",
        "자동화_오류": "자동화 스케줄 로그 정상, 앱 권한 이슈 의심",
    }
    return logs.get(category, "관련 로그 없음")

@tool
def search_solution_db(category: str) -> str:
    """카테고리별 기존 해결책을 검색합니다 (RAG 역할)."""
    solutions = {
        "연결_오류":  "1) 공유기 재부팅 2) 기기 위치 확인 3) 중계기 설치 권장",
        "배터리_부족": "기기 후면 커버 열고 AA 배터리 4개 교체",
        "제어_오류":  "앱 재시작 후 기기 재등록, 펌웨어 업데이트 확인",
        "자동화_오류": "앱 설정 > 권한 > 위치 권한 허용 후 스케줄 재등록",
    }
    return solutions.get(category, "해결책 DB에 없음 — 전문 상담 필요")

@tool
def assign_to_agent(channel: str, voc: str, draft: str) -> str:
    """Slack으로 담당자에게 VOC와 답변 초안을 전달합니다."""
    print(f"\n  [Slack #{channel}]")
    print(f"  VOC: {voc[:40]}...")
    print(f"  초안: {draft[:60]}...")
    return "담당자에게 전달 완료"

tools = [classify_voc, search_device_logs, search_solution_db, assign_to_agent]

# ── State & 노드 ──────────────────────────────────────────────────────
class VocState(TypedDict):
    messages: Annotated[list, operator.add]

SYSTEM = SystemMessage(content="""당신은 스마트홈 CS 자동화 AI 에이전트입니다.

고객 문의 처리 순서:
1. classify_voc → 카테고리/심각도 파악
2. search_device_logs → 관련 로그 조회
3. search_solution_db → 해결책 검색
4. 답변 초안 작성 (로그 + 해결책 기반)
5. assign_to_agent → #cs-team 채널로 전달

심각도 "높"이면 #cs-urgent 채널 사용.""")

llm_with_tools = llm.bind_tools(tools)

def agent(state: VocState) -> VocState:
    response = llm_with_tools.invoke([SYSTEM] + state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)

graph = StateGraph(VocState)
graph.add_node("agent", agent)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tools_condition)
graph.add_edge("tools", "agent")

app = graph.compile()

# ── 실행 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("VOC 자동화 에이전트")
    print("=" * 55)

    voc_list = [
        "거실 에어컨이 계속 꺼져요. 앱에서도 오프라인으로 뜨고요.",
        "현관 도어락 배터리가 없다고 경고가 떠요.",
    ]

    for voc in voc_list:
        print(f"\n고객 문의: {voc}")
        print("-" * 55)

        result = app.invoke({"messages": [HumanMessage(content=f"고객 문의: {voc}")]})
        print(f"\n처리 결과:\n{result['messages'][-1].content}")
        print("=" * 55)
