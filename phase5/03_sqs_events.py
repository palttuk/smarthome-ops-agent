"""
Phase 5 - Step 3: SQS 이벤트 기반 처리
기기 이벤트 → 큐에 적재 → Lambda가 비동기 처리

실행: python phase5/03_sqs_events.py
"""
import boto3
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

QUEUE_URL = os.getenv("SQS_QUEUE_URL", "")


def get_sqs():
    return boto3.client("sqs", region_name=os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2"))


def enqueue_device_event(device_id: str, event_type: str, details: dict = None) -> str:
    """기기 이벤트를 SQS에 적재"""
    sqs = get_sqs()
    message = {
        "device_id":  device_id,
        "event_type": event_type,        # OFFLINE, ERROR, BATTERY_LOW, ...
        "details":    details or {},
        "timestamp":  datetime.now().isoformat()
    }

    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message, ensure_ascii=False),
        MessageAttributes={
            "event_type": {
                "StringValue": event_type,
                "DataType":    "String"
            }
        }
    )
    print(f"  [SQS] 적재 완료: MessageId={response['MessageId'][:8]}...")
    return response["MessageId"]


def consume_events(max_messages: int = 5) -> list[dict]:
    """SQS에서 이벤트 수신 (Lambda가 자동으로 처리하지만 수동 테스트용)"""
    sqs = get_sqs()
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=5
    )

    messages = []
    for msg in response.get("Messages", []):
        body = json.loads(msg["Body"])
        print(f"  [수신] {body['device_id']} — {body['event_type']}")
        messages.append(body)

        # 처리 완료 후 삭제
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=msg["ReceiptHandle"]
        )

    return messages


# ── SQS 없이 동작 확인하는 Mock 데모 ─────────────────────────────────
def mock_demo():
    print("SQS 이벤트 패턴 데모 (Mock)\n" + "=" * 50)

    # 메모리 큐로 시뮬레이션
    queue = []

    def mock_enqueue(device_id, event_type, details=None):
        event = {
            "device_id":  device_id,
            "event_type": event_type,
            "details":    details or {},
            "timestamp":  datetime.now().isoformat()
        }
        queue.append(event)
        print(f"  [Enqueue] {device_id} — {event_type}")

    def mock_consume():
        if not queue:
            print("  [Queue] 비어있음")
            return []
        events = queue.copy()
        queue.clear()
        return events

    # 이벤트 발생 시뮬레이션
    print("[ 이벤트 발생 ]")
    mock_enqueue("device_003", "OFFLINE", {"last_seen": "52분 전"})
    mock_enqueue("device_001", "BATTERY_LOW", {"level": 12})
    mock_enqueue("device_004", "ERROR", {"code": "CONNECTION_LOST"})

    print(f"\n[ 큐 상태: {len(queue)}개 ]")

    # Lambda가 처리하는 방식 시뮬레이션
    print("\n[ Lambda 처리 시뮬레이션 ]")
    events = mock_consume()
    for event in events:
        _process_event(event)

    print(f"\n💡 실제 배포 시 Lambda가 SQS 트리거로 자동 처리")
    print("   template.yaml에서 SQS → Lambda 이벤트 소스 설정")


def _process_event(event: dict):
    """이벤트 타입별 에이전트 호출 (실제로는 Phase 4 에이전트)"""
    device_id  = event["device_id"]
    event_type = event["event_type"]

    action_map = {
        "OFFLINE":     f"Jira High 티켓 + Slack 알림",
        "BATTERY_LOW": f"Slack 배터리 교체 안내",
        "ERROR":       f"에러 로그 분석 + Jira Medium 티켓",
    }

    action = action_map.get(event_type, "로깅만")
    print(f"  [{device_id}] {event_type} → {action}")


if __name__ == "__main__":
    if os.getenv("SQS_QUEUE_URL"):
        # 실제 SQS
        enqueue_device_event("device_003", "OFFLINE", {"last_seen": "52분 전"})
        consume_events()
    else:
        mock_demo()
