"""
Phase 5 - Step 4: 전체 아키텍처 통합 시뮬레이션
AWS 없이 전체 흐름을 로컬에서 end-to-end 체험

실행: python phase5/04_architecture.py
"""
import json
import time
import sys
import os
from datetime import datetime
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── 로컬 시뮬레이션 클래스 ─────────────────────────────────────────────
class LocalS3:
    """S3 시뮬레이션 (메모리)"""
    def __init__(self):
        self._store = {}

    def put(self, key: str, body: str):
        self._store[key] = {"body": body, "uploaded_at": datetime.now().isoformat()}
        print(f"  [S3] PUT s3://smarthome-ai-data/{key}")

    def get(self, key: str) -> str | None:
        return self._store.get(key, {}).get("body")

    def list(self, prefix: str) -> list[str]:
        return [k for k in self._store if k.startswith(prefix)]


class LocalSQS:
    """SQS 시뮬레이션 (메모리 큐)"""
    def __init__(self):
        self._queue = deque()

    def send(self, message: dict):
        self._queue.append(message)
        print(f"  [SQS] Enqueue: {message['device_id']} — {message['event_type']}")

    def receive(self, max_count: int = 5) -> list[dict]:
        messages = []
        while self._queue and len(messages) < max_count:
            messages.append(self._queue.popleft())
        return messages


class LocalSecrets:
    """Secrets Manager 시뮬레이션"""
    def get(self, key: str) -> str:
        return os.getenv(key, f"mock_{key}")


# ── 에이전트 (Phase 4 핵심 로직 인라인) ──────────────────────────────
def run_ops_agent(prompt: str, s3: LocalS3) -> dict:
    """Phase 4 에이전트 로직 (실제로는 import해서 사용)"""
    from dotenv import load_dotenv
    load_dotenv()

    import anthropic
    client = anthropic.Anthropic()

    TOOLS = [
        {
            "name": "get_device_status",
            "description": "기기 상태 조회",
            "input_schema": {
                "type": "object",
                "properties": {"device_id": {"type": "string"}},
                "required": ["device_id"]
            }
        },
        {
            "name": "create_jira_ticket",
            "description": "Jira 티켓 생성",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary":  {"type": "string"},
                    "priority": {"type": "string"}
                },
                "required": ["summary", "priority"]
            }
        }
    ]

    def get_device_status(device_id):
        db = {
            "device_003": {"status": "offline", "type": "거실 에어컨", "last_seen": "52분 전"},
            "device_001": {"status": "online",  "type": "현관 도어락"},
        }
        return json.dumps(db.get(device_id, {"status": "not_found"}), ensure_ascii=False)

    def create_jira_ticket(summary, priority="High"):
        ticket = f"SMART-{abs(hash(summary)) % 9999:04d}"
        s3.put(f"tickets/{ticket}.json", json.dumps({"summary": summary, "priority": priority}))
        return json.dumps({"ticket_id": ticket, "priority": priority})

    tool_map = {"get_device_status": get_device_status, "create_jira_ticket": create_jira_ticket}

    messages = [{"role": "user", "content": prompt}]
    while True:
        resp = client.messages.create(
            model="claude-opus-4-7", max_tokens=1024,
            tools=TOOLS, messages=messages
        )
        if resp.stop_reason == "end_turn":
            return {"result": resp.content[0].text}

        if resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    out = tool_map[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": out
                    })
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user",      "content": tool_results})


# ── Lambda 핸들러 (로컬 시뮬레이션) ──────────────────────────────────
def lambda_handler(event: dict, s3: LocalS3, secrets: LocalSecrets) -> dict:
    source = "sqs" if "Records" in event else "api_gateway"

    if source == "api_gateway":
        body    = json.loads(event.get("body", "{}"))
        prompt  = body.get("message", "device_003 상태 확인하고 처리해줘")
        result  = run_ops_agent(prompt, s3)
        s3.put(f"results/{datetime.now().strftime('%H%M%S')}.json", json.dumps(result))
        return {"statusCode": 200, "body": json.dumps(result)}

    elif source == "sqs":
        for record in event["Records"]:
            msg    = json.loads(record["body"])
            prompt = f"{msg['device_id']}가 {msg['event_type']} 상태입니다. 처리해주세요."
            result = run_ops_agent(prompt, s3)
            print(f"  처리 결과: {result['result'][:60]}...")
        return {"statusCode": 200}


# ── 전체 아키텍처 시뮬레이션 ──────────────────────────────────────────
def run_full_simulation():
    print("전체 아키텍처 End-to-End 시뮬레이션")
    print("=" * 55)
    print()
    print("아키텍처:")
    print("  IoT 기기 → SQS → Lambda → [S3 저장, Jira, Slack]")
    print("  Slack     → API Gateway → Lambda → [S3 저장]")
    print()

    s3      = LocalS3()
    sqs     = LocalSQS()
    secrets = LocalSecrets()

    # ── 시나리오 1: IoT 기기 이벤트 → SQS → Lambda ───────────────
    print("[ 시나리오 1: SQS 이벤트 기반 자동 처리 ]")
    sqs.send({"device_id": "device_003", "event_type": "OFFLINE",
              "timestamp": datetime.now().isoformat()})

    events = sqs.receive()
    sqs_event = {
        "Records": [{"body": json.dumps(e)} for e in events]
    }

    print("\nLambda 실행 중...")
    lambda_handler(sqs_event, s3, secrets)

    # ── 시나리오 2: API Gateway → Lambda ─────────────────────────
    print("\n[ 시나리오 2: API Gateway 직접 호출 ]")
    api_event = {
        "requestContext": {},
        "body": json.dumps({"message": "device_003 상태 점검해줘"})
    }

    print("\nLambda 실행 중...")
    result = lambda_handler(api_event, s3, secrets)
    print(f"\n응답: {result['statusCode']} OK")

    # ── S3 저장 현황 ───────────────────────────────────────────────
    print(f"\n[ S3 저장 현황 ]")
    all_keys = s3.list("")
    for key in all_keys:
        print(f"  s3://smarthome-ai-data/{key}")

    print("\n✅ 전체 아키텍처 시뮬레이션 완료")


if __name__ == "__main__":
    run_full_simulation()
