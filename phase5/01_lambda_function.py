"""
Phase 5 - Step 1: Lambda 함수 (배포 가능한 형태)
Phase 4의 에이전트를 Lambda로 감싸는 패턴

실제 배포 시:
  sam build && sam deploy --guided

로컬 테스트:
  python phase5/01_lambda_function.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Lambda 핸들러 ──────────────────────────────────────────────────────
def lambda_handler(event: dict, context=None) -> dict:
    """
    API Gateway / Slack / SQS 등 모든 이벤트를 받는 진입점.
    이벤트 소스에 따라 분기 처리.
    """
    source = _detect_source(event)

    try:
        if source == "api_gateway":
            return _handle_api_gateway(event)
        elif source == "sqs":
            return _handle_sqs(event)
        elif source == "slack":
            return _handle_slack(event)
        else:
            return _response(400, {"error": f"알 수 없는 이벤트 소스: {source}"})

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return _response(500, {"error": str(e)})


def _detect_source(event: dict) -> str:
    if "Records" in event and event["Records"][0].get("eventSource") == "aws:sqs":
        return "sqs"
    if "requestContext" in event:
        return "api_gateway"
    if event.get("type") == "slack":
        return "slack"
    return "unknown"


def _handle_api_gateway(event: dict) -> dict:
    body = json.loads(event.get("body") or "{}")
    user_message = body.get("message", "")
    device_id    = body.get("device_id", "")

    if not user_message and not device_id:
        return _response(400, {"error": "message 또는 device_id 필요"})

    # 실제로는 Phase 4 에이전트 호출
    prompt = user_message or f"{device_id} 상태 확인하고 문제있으면 처리해줘"
    result = _run_agent(prompt)

    return _response(200, {"result": result})


def _handle_sqs(event: dict) -> dict:
    processed = []
    for record in event["Records"]:
        message = json.loads(record["body"])
        device_id   = message.get("device_id", "")
        event_type  = message.get("event_type", "")

        print(f"[SQS] {device_id} — {event_type}")

        if event_type in ("OFFLINE", "ERROR"):
            result = _run_agent(f"{device_id}가 {event_type} 상태입니다. 처리해주세요.")
            processed.append({"device_id": device_id, "result": result})

    return {"statusCode": 200, "processed": len(processed)}


def _handle_slack(event: dict) -> dict:
    text    = event.get("text", "")
    channel = event.get("channel", "#general")

    result = _run_agent(f"Slack 요청 (채널: {channel}): {text}")
    return _response(200, {"result": result})


def _run_agent(prompt: str) -> str:
    """Phase 4 에이전트 호출 (실제 배포 시 import해서 사용)"""
    # 로컬 테스트용 mock
    return f"[에이전트 처리 완료] '{prompt[:40]}...' → Jira 티켓 생성, Slack 알림 전송"


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False)
    }


# ── 로컬 테스트 ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Lambda 함수 로컬 테스트\n" + "=" * 50)

    # API Gateway 이벤트 시뮬레이션
    api_event = {
        "requestContext": {"httpMethod": "POST"},
        "body": json.dumps({"device_id": "device_003"})
    }
    result = lambda_handler(api_event)
    print(f"[API Gateway]\n{json.dumps(result, ensure_ascii=False, indent=2)}")

    # SQS 이벤트 시뮬레이션
    sqs_event = {
        "Records": [{
            "eventSource": "aws:sqs",
            "body": json.dumps({
                "device_id": "device_003",
                "event_type": "OFFLINE",
                "timestamp": "2026-05-08T10:00:00Z"
            })
        }]
    }
    result = lambda_handler(sqs_event)
    print(f"\n[SQS]\n{json.dumps(result, ensure_ascii=False, indent=2)}")
