"""
Phase 3 - Step 3: 실제 Slack 연동
실행 전 .env에 추가:
  SLACK_BOT_TOKEN=xoxb-...
  SLACK_CHANNEL=#your-channel

Slack App 만들기:
  1. https://api.slack.com/apps → Create New App
  2. OAuth & Permissions → Bot Token Scopes: chat:write
  3. Install to Workspace → Bot User OAuth Token 복사

실행: python phase3/03_real_slack.py
"""
import os
import anthropic
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

claude = anthropic.Anthropic()
slack  = WebClient(token=os.getenv("SLACK_BOT_TOKEN", ""))
CHANNEL = os.getenv("SLACK_CHANNEL", "#general")


def send_slack_message(channel: str, message: str, severity: str = "info") -> dict:
    """실제 Slack API 호출"""
    if not os.getenv("SLACK_BOT_TOKEN"):
        print(f"  [Slack MOCK] #{channel} ({severity}): {message[:50]}...")
        return {"ok": True, "mock": True}

    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "📢")
    try:
        result = slack.chat_postMessage(
            channel=channel,
            text=f"{emoji} {message}",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *[{severity.upper()}]*\n{message}"
                }
            }]
        )
        print(f"  [Slack] 전송 성공 ts={result['ts']}")
        return {"ok": True, "ts": result["ts"]}
    except SlackApiError as e:
        print(f"  [Slack] 전송 실패: {e.response['error']}")
        return {"ok": False, "error": e.response["error"]}


TOOLS = [{
    "name": "send_slack_alert",
    "description": "Slack 채널에 스마트홈 장애 알림을 전송합니다",
    "input_schema": {
        "type": "object",
        "properties": {
            "channel":  {"type": "string"},
            "message":  {"type": "string"},
            "severity": {"type": "string", "enum": ["info", "warning", "critical"]}
        },
        "required": ["channel", "message"]
    }
}]


def run(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = claude.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return response.content[0].text

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = send_slack_message(**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user",      "content": tool_results})


if __name__ == "__main__":
    channel = os.getenv("SLACK_CHANNEL", "#smarthome-alerts")
    result = run(
        f"device_003 거실 에어컨이 47분째 오프라인입니다. "
        f"{channel} 채널에 critical 알림을 보내주세요."
    )
    print(result)
