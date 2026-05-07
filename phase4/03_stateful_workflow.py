"""
Phase 4 - Step 3: 상태 기반 복잡 워크플로우
State에 도메인 데이터를 담아 단계별로 처리
실행: python phase4/03_stateful_workflow.py
"""
import operator
from typing import Annotated
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()
llm = ChatAnthropic(model="claude-opus-4-7", max_tokens=1024)

# ── 도메인 특화 State ─────────────────────────────────────────────────
class OpsState(TypedDict):
    device_ids:    list[str]
    check_results: Annotated[list, operator.add]   # 조회 결과 누적
    issues:        Annotated[list, operator.add]   # 문제 기기 누적
    actions_taken: Annotated[list, operator.add]   # 처리 이력 누적
    report:        str

# ── Mock 데이터 ───────────────────────────────────────────────────────
DEVICE_DB = {
    "device_001": {"status": "online",  "type": "현관 도어락", "signal": -62},
    "device_002": {"status": "online",  "type": "안방 조명",   "signal": -70},
    "device_003": {"status": "offline", "type": "거실 에어컨", "last_seen": "52분 전"},
    "device_004": {"status": "offline", "type": "주방 환풍기", "last_seen": "3분 전"},
}

# ── 노드 함수들 ───────────────────────────────────────────────────────
def check_devices(state: OpsState) -> OpsState:
    """모든 기기 상태 조회"""
    print("\n[Node] 기기 상태 조회 중...")
    results = []
    for did in state["device_ids"]:
        info = DEVICE_DB.get(did, {"status": "not_found"})
        results.append({"device_id": did, **info})
        print(f"  {did}: {info['status']}")
    return {"check_results": results}

def filter_issues(state: OpsState) -> OpsState:
    """오프라인 기기 필터링"""
    issues = [r for r in state["check_results"] if r["status"] == "offline"]
    print(f"\n[Node] 이슈 기기: {len(issues)}개")
    return {"issues": issues}

def handle_issues(state: OpsState) -> OpsState:
    """이슈 기기별 자동 처리"""
    actions = []
    for issue in state["issues"]:
        did  = issue["device_id"]
        mins = int(issue.get("last_seen", "0분 전").replace("분 전", ""))
        priority = "Highest" if mins >= 30 else "High"

        ticket = f"SMART-{hash(did) % 9999:04d}"
        print(f"\n[Node] {did} 처리 중...")
        print(f"  Jira 티켓 생성: {ticket} ({priority})")
        print(f"  Slack #smarthome-ops 알림 전송")

        actions.append({
            "device_id": did,
            "ticket":    ticket,
            "priority":  priority,
            "slack":     "전송 완료"
        })
    return {"actions_taken": actions}

def generate_report(state: OpsState) -> OpsState:
    """LLM으로 최종 보고서 생성"""
    print("\n[Node] 보고서 생성 중...")

    prompt = f"""다음 스마트홈 운영 점검 결과를 3줄 요약으로 작성하세요.

점검 기기: {[r['device_id'] for r in state['check_results']]}
이슈 발견: {len(state['issues'])}건 — {[i['device_id'] for i in state['issues']]}
처리 완료: Jira {[a['ticket'] for a in state['actions_taken']]} 생성, Slack 알림 완료"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"report": response.content}

def has_issues(state: OpsState) -> str:
    """이슈가 있으면 handle, 없으면 report로 바로"""
    return "handle" if state["issues"] else "report"

# ── 그래프 구성 ───────────────────────────────────────────────────────
workflow = StateGraph(OpsState)
workflow.add_node("check",  check_devices)
workflow.add_node("filter", filter_issues)
workflow.add_node("handle", handle_issues)
workflow.add_node("report", generate_report)

workflow.set_entry_point("check")
workflow.add_edge("check",  "filter")
workflow.add_conditional_edges("filter", has_issues, {"handle": "handle", "report": "report"})
workflow.add_edge("handle", "report")
workflow.add_edge("report", END)

app = workflow.compile()

if __name__ == "__main__":
    print("상태 기반 워크플로우 실행")
    print("=" * 50)

    result = app.invoke({
        "device_ids":    ["device_001", "device_002", "device_003", "device_004"],
        "check_results": [],
        "issues":        [],
        "actions_taken": [],
        "report":        ""
    })

    print(f"\n{'='*50}")
    print("최종 보고서:")
    print(result["report"])
