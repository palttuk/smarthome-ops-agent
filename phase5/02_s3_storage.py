"""
Phase 5 - Step 2: S3 스토리지 연동
로그 업로드, 매뉴얼 다운로드, 분석 결과 저장

실행 전 .env에 추가:
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_DEFAULT_REGION=ap-northeast-2
  S3_BUCKET=smarthome-ai-data

실행: python phase5/02_s3_storage.py
"""
import boto3
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.getenv("S3_BUCKET", "smarthome-ai-data")


def get_s3():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")
    )


def upload_log(device_id: str, log_content: str) -> str:
    """기기 로그를 S3에 날짜별로 저장"""
    s3  = get_s3()
    now = datetime.now()
    key = f"logs/{device_id}/{now.strftime('%Y/%m/%d/%H%M%S')}.txt"

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=log_content.encode("utf-8"),
        ContentType="text/plain",
        Metadata={
            "device_id": device_id,
            "uploaded_at": now.isoformat()
        }
    )
    print(f"  업로드 완료: s3://{BUCKET}/{key}")
    return f"s3://{BUCKET}/{key}"


def save_analysis_result(device_id: str, result: dict) -> str:
    """에이전트 분석 결과를 JSON으로 S3에 저장"""
    s3  = get_s3()
    now = datetime.now()
    key = f"analysis/{device_id}/{now.strftime('%Y/%m/%d/%H%M%S')}.json"

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json"
    )
    print(f"  분석 결과 저장: s3://{BUCKET}/{key}")
    return f"s3://{BUCKET}/{key}"


def list_device_logs(device_id: str, date: str = None) -> list[str]:
    """기기 로그 목록 조회 (date: 'YYYY/MM/DD')"""
    s3     = get_s3()
    prefix = f"logs/{device_id}/{date or ''}"

    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    keys = [obj["Key"] for obj in response.get("Contents", [])]
    print(f"  '{prefix}' 하위 로그: {len(keys)}개")
    return keys


def download_manual(device_type: str) -> str:
    """기기 매뉴얼 S3에서 /tmp로 다운로드"""
    s3    = get_s3()
    key   = f"manuals/{device_type}/manual.pdf"
    local = f"/tmp/{device_type}_manual.pdf"

    try:
        s3.download_file(BUCKET, key, local)
        print(f"  매뉴얼 다운로드 완료: {local}")
        return local
    except s3.exceptions.NoSuchKey:
        print(f"  매뉴얼 없음: {key}")
        return ""


# ── S3 연동 없이 동작 확인하는 Mock 테스트 ────────────────────────────
def mock_demo():
    print("S3 패턴 데모 (Mock)\n" + "=" * 50)

    # 실제 S3 대신 파일 시스템으로 시뮬레이션
    import tempfile, pathlib
    base = pathlib.Path(tempfile.mkdtemp())

    device_id = "device_003"
    log_key   = f"logs/{device_id}/2026/05/08/100000.txt"
    log_path  = base / log_key
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 로그 저장
    sample_log = "10:23 ERROR CONNECTION_LOST\n10:35 ERROR CONNECTION_LOST\n10:50 ERROR TIMEOUT"
    log_path.write_text(sample_log)
    print(f"[Upload] s3://{BUCKET}/{log_key}")

    # 분석 결과 저장
    result_key  = f"analysis/{device_id}/2026/05/08/100000.json"
    result_path = base / result_key
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result = {"severity": "HIGH", "root_cause": "Wi-Fi 신호 약화", "device_id": device_id}
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[Save]   s3://{BUCKET}/{result_key}")

    # 목록 조회
    logs = list(base.glob(f"logs/{device_id}/**/*.txt"))
    print(f"[List]   {device_id} 로그 {len(logs)}개 발견")

    print(f"\n💡 실제 AWS 연동 시 mock_demo() → 실제 함수(upload_log 등)로 교체")


if __name__ == "__main__":
    if os.getenv("AWS_ACCESS_KEY_ID"):
        # 실제 AWS 연동
        log_path = upload_log("device_003", "10:23 ERROR CONNECTION_LOST")
        save_analysis_result("device_003", {"severity": "HIGH"})
    else:
        # Mock 데모
        mock_demo()
