"""
Phase 3 - 실습 프로젝트: 운영 자동화 에이전트
"device_003 확인하고 문제있으면 처리해줘" 한 마디로
→ 상태 조회 → 에러 로그 확인 → Jira 티켓 → Slack 알림까지 자동 처리

실행: python phase3/04_ops_agent.py
"""
import anthropic
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

TOOLS = [
    {
        "name": "get_device_status",
        "description": "스마트홈 기기 현재 상태 조회 (online/offline, 신호 강도)",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"}
            },
            "required": ["device_id"]
        }
    },
    {
        "name": "get_error_logs",
        "description": "기기의 최근 에러 로그 조회",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"},
                "hours": {"type": "integer", "description": "최근 N시간 (기본 1)"}
            },
            "required": ["device_id"]
        }
    },
    {
        "name": "create_jira_ticket",
        "description": "장애 Jira 티켓 생성. 오프라인 기기는 반드시 생성할 것.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary":     {"type": "string"},
                "description": {"type": "string"},
                "priority":    {"type": "string", "enum": ["Highest", "High", "Medium", "Low"]}
            },
            "required": ["summary", "description", "priority"]
        }
    },
    {
        "name": "send_slack_alert",
        "description": "운영팀 Slack 채널에 알림 전송",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel":  {"type": "string"},
                "message":  {"type": "string"},
                "severity": {"type": "string", "enum": ["info", "warning", "critical"]}
            },
            "required": ["channel", "message", "severity"]
        }
    },
]

SYSTEM = """당신은 스마트홈 운영 자동화 AI 에이전트입니다.

## 처리 규칙
1. 기기 상태 확인
2. offline이면 → 에러 로그 조회
3. 에러 로그 기반으로 원인 판단
4. Jira 티켓 생성 (priority: 30분+ offline → High, 1시간+ → Highest)
5. #smarthome-ops Slack에 요약 알림

## 응답 형식
모든 처리 완료 후 다음 형식으로 요약:
- 기기: [ID] ([상태])
- 원인: [판단한 원인]
- 조치: Jira [티켓ID] 생성, Slack 알림 완료"""


# ── Mock 구현 ─────────────────────────────────────────────────────────
def get_device_status(device_id: str) -> dict:
    db = {
        "device_003": {
            "status": "offline",
            "device_type": "거실 에어컨",
            "last_seen": "47분 전",
            "firmware": "v2.1.3"
        },
        "device_001": {
            "status": "online",
            "device_type": "현관 도어락",
            "signal_dbm": -62,
            "uptime": "3일"
        },
    }
    return db.get(device_id, {"status": "not_found"})


def get_error_logs(device_id: str, hours: int = 1) -> dict:
    if device_id == "device_003":
        return {
            "device_id": device_id,
            "period": f"최근 {hours}시간",
            "errors": [
                {"time": "10:23", "code": "CONNECTION_LOST", "signal_dbm": -85},
                {"time": "10:35", "code": "CONNECTION_LOST", "signal_dbm": -91},
                {"time": "10:50", "code": "TIMEOUT",         "signal_dbm": -95},
            ],
            "pattern": "신호 강도 지속 약화 (-85 → -95dBm)"
        }
    return {"device_id": device_id, "period": f"최근 {hours}시간", "errors": []}


def create_jira_ticket(summary: str, description: str, priority: str) -> dict:
    ticket_id = f"SMART-{datetime.now().strftime('%H%M%S')}"
    print(f"\n  ✅ Jira 티켓 생성")
    print(f"     ID: {ticket_id}")
    print(f"     우선순위: {priority}")
    print(f"     제목: {summary}")
    return {
        "ticket_id": ticket_id,
        "url": f"https://jira.company.com/browse/{ticket_id}",
        "priority": priority
    }


def send_slack_alert(channel: str, message: str, severity: str) -> dict:
    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "📢")
    print(f"\n  ✅ Slack 알림 전송")
    print(f"     채널: #{channel}")
    print(f"     {emoji} {message[:80]}")
    return {"ok": True, "channel": channel}


TOOL_MAP = {
    "get_device_status":  get_device_status,
    "get_error_logs":     get_error_logs,
    "create_jira_ticket": create_jira_ticket,
    "send_slack_alert":   send_slack_alert,
}


def run_agent(user_request: str) -> str:
    messages = [{"role": "user", "content": user_request}]
    step = 0

    while True:
        step += 1
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2048,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return response.content[0].text

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n[Step {step}] {block.name}")
                    result = TOOL_MAP[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user",      "content": tool_results})


if __name__ == "__main__":
    print("=" * 60)
    print("운영 자동화 에이전트")
    print("=" * 60)

    request = "device_003 상태 확인하고 문제있으면 알아서 처리해줘"
    print(f"\n요청: {request}\n")

    summary = run_agent(request)
    print(f"\n{'='*60}")
    print("처리 완료 요약:")
    print(summary)
