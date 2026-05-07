"""
Phase 3 - Step 1: Function Calling 기초
LLM이 스스로 어떤 도구를 쓸지 판단하는 원리 이해
실행: python phase3/01_tool_use_basic.py
"""
import anthropic
import json
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

# ── 1. 도구 정의 (LLM에게 "이런 도구들이 있어"라고 알려주는 것) ──────────
TOOLS = [
    {
        "name": "get_device_status",
        "description": "스마트홈 기기의 현재 상태를 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "기기 ID (예: device_001)"
                }
            },
            "required": ["device_id"]
        }
    },
    {
        "name": "restart_device",
        "description": "오프라인 기기를 원격으로 재시작합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"},
                "reason": {"type": "string", "description": "재시작 사유"}
            },
            "required": ["device_id"]
        }
    },
    {
        "name": "get_recent_errors",
        "description": "기기의 최근 에러 로그를 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"},
                "hours": {"type": "integer", "description": "조회할 시간 범위 (기본 24시간)"}
            },
            "required": ["device_id"]
        }
    }
]


# ── 2. 실제 함수 구현 (지금은 mock, 나중에 실제 API로 교체) ──────────
def get_device_status(device_id: str) -> dict:
    mock = {
        "device_001": {"status": "online",  "signal": -62, "uptime": "3일 12시간"},
        "device_002": {"status": "online",  "signal": -70, "uptime": "1일 4시간"},
        "device_003": {"status": "offline", "last_seen": "47분 전", "error_count": 5},
    }
    return mock.get(device_id, {"status": "unknown", "error": "기기를 찾을 수 없습니다"})


def restart_device(device_id: str, reason: str = "") -> dict:
    print(f"  [도구 실행] {device_id} 재시작 요청 — 사유: {reason}")
    return {"success": True, "message": f"{device_id} 재시작 신호 전송됨 (예상 복구 30초)"}


def get_recent_errors(device_id: str, hours: int = 24) -> dict:
    if device_id == "device_003":
        return {
            "errors": [
                {"time": "10:23", "code": "CONNECTION_LOST", "signal": -85},
                {"time": "10:35", "code": "CONNECTION_LOST", "signal": -91},
                {"time": "10:50", "code": "TIMEOUT",         "signal": -95},
            ],
            "total": 5,
            "period_hours": hours
        }
    return {"errors": [], "total": 0, "period_hours": hours}


TOOL_MAP = {
    "get_device_status":  get_device_status,
    "restart_device":     restart_device,
    "get_recent_errors":  get_recent_errors,
}


# ── 3. 에이전트 루프 ──────────────────────────────────────────────────
def run(user_message: str) -> str:
    print(f"\n사용자: {user_message}")
    print("-" * 50)
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )

        # 도구 호출 없이 바로 답변
        if response.stop_reason == "end_turn":
            return response.content[0].text

        # 도구 호출 처리
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [LLM 판단] {block.name}({json.dumps(block.input, ensure_ascii=False)})")
                    result = TOOL_MAP[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user",      "content": tool_results})


if __name__ == "__main__":
    tests = [
        "device_003 상태 확인해줘",
        "device_003 확인하고 문제있으면 재시작해줘",
        "device_001이랑 device_003 둘 다 상태 알려줘",
    ]

    for msg in tests:
        answer = run(msg)
        print(f"\nAI: {answer}")
        print("=" * 60)
