"""
Phase 3 - Step 2: 여러 도구를 조합하는 에이전트
Slack + Jira 연동 (mock) — 실제 토큰 없이 전체 흐름 체험
실행: python phase3/02_multi_tool_agent.py
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
        "description": "스마트홈 기기 상태 조회",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"}
            },
            "required": ["device_id"]
        }
    },
    {
        "name": "create_jira_ticket",
        "description": "장애 Jira 티켓 생성",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary":     {"type": "string", "description": "티켓 제목"},
                "description": {"type": "string", "description": "상세 내용"},
                "priority":    {"type": "string", "enum": ["Highest", "High", "Medium", "Low"]}
            },
            "required": ["summary", "description"]
        }
    },
    {
        "name": "send_slack_alert",
        "description": "Slack 채널에 알림 전송",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel":  {"type": "string", "description": "#채널명"},
                "message":  {"type": "string"},
                "severity": {"type": "string", "enum": ["info", "warning", "critical"]}
            },
            "required": ["channel", "message"]
        }
    },
]


# ── Mock 구현 (실제 API 키 없이 흐름 체험) ───────────────────────────
def get_device_status(device_id: str) -> dict:
    db = {
        "device_003": {"status": "offline", "last_seen": "47분 전", "type": "거실 에어컨"},
        "device_001": {"status": "online",  "signal": -62,          "type": "현관 도어락"},
    }
    return db.get(device_id, {"status": "unknown"})


def create_jira_ticket(summary: str, description: str, priority: str = "Medium") -> dict:
    ticket_id = f"SMART-{datetime.now().strftime('%H%M%S')}"
    print(f"  [Jira] 티켓 생성: {ticket_id} / {priority} / {summary}")
    return {"ticket_id": ticket_id, "url": f"https://jira.example.com/browse/{ticket_id}", "priority": priority}


def send_slack_alert(channel: str, message: str, severity: str = "info") -> dict:
    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "📢")
    print(f"  [Slack] #{channel} {emoji} {message[:60]}...")
    return {"ok": True, "channel": channel}


TOOL_MAP = {
    "get_device_status": get_device_status,
    "create_jira_ticket": create_jira_ticket,
    "send_slack_alert": send_slack_alert,
}

SYSTEM = """당신은 스마트홈 운영 자동화 AI 에이전트입니다.

기기 문제 발견 시 자동 처리 규칙:
- 오프라인 기기 → Jira 티켓(High) + #smarthome-alerts Slack 알림
- 온라인 기기   → 상태만 보고

간결하게 처리하고 완료 요약을 한 문단으로 전달하세요."""


def run(user_message: str) -> str:
    print(f"\n요청: {user_message}")
    print("-" * 50)
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
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
                    print(f"  → {block.name}({json.dumps(block.input, ensure_ascii=False)})")
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
    print("멀티 도구 에이전트 (Slack + Jira 연동)")
    print("=" * 60)

    result = run("device_001이랑 device_003 상태 확인하고 문제있는 거 처리해줘")
    print(f"\n완료 보고:\n{result}")
