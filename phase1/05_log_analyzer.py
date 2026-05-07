"""
Phase 1 - Step 5: 실습 프로젝트 - 로그 분석기
실행: python phase1/05_log_analyzer.py [로그파일경로]
      python phase1/05_log_analyzer.py  (인자 없으면 샘플 로그 사용)
"""
import anthropic
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

SYSTEM_PROMPT = """
당신은 스마트홈 시스템 장애 분석 전문가입니다.
로그를 분석하여 반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요.

{
  "severity": "HIGH | MEDIUM | LOW",
  "root_cause": "근본 원인 (한 문장)",
  "affected_devices": ["기기 ID 목록"],
  "pattern": "에러 패턴 설명",
  "recommended_actions": ["조치 사항 1", "조치 사항 2"],
  "prevent_recurrence": "재발 방지 방법"
}
"""

SAMPLE_LOG = """
2026-05-07 10:20:01 INFO  gateway    공유기 재부팅 완료
2026-05-07 10:23:01 ERROR device_003 CONNECTION_LOST (신호: -85dBm)
2026-05-07 10:23:10 ERROR device_003 CONNECTION_LOST (신호: -87dBm)
2026-05-07 10:23:20 ERROR device_003 CONNECTION_LOST (신호: -91dBm)
2026-05-07 10:23:25 WARN  device_003 재연결 실패 - 대기 중
2026-05-07 10:35:00 ERROR device_003 CONNECTION_LOST (신호: -93dBm)
2026-05-07 10:35:05 ERROR device_003 TIMEOUT
2026-05-07 10:50:01 ERROR device_003 CONNECTION_LOST (신호: -95dBm)
"""


def load_log(file_path: str | None) -> str:
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return SAMPLE_LOG


def filter_important(log: str) -> str:
    """ERROR/WARN 레벨만 추출 (토큰 절약)"""
    lines = [
        line for line in log.splitlines()
        if any(level in line for level in ["ERROR", "WARN", "CRITICAL"])
    ]
    return "\n".join(lines[-100:])  # 최근 100줄


def analyze(log: str) -> dict:
    filtered = filter_important(log)

    prompt = f"""
## 기기 로그 (ERROR/WARN 필터링)
{filtered}

## 분석 시각
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # JSON 파싱 시도
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # JSON 블록만 추출
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])


def print_result(result: dict):
    severity_emoji = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "ℹ️"}
    emoji = severity_emoji.get(result["severity"], "📋")

    print(f"\n{emoji} 심각도: {result['severity']}")
    print(f"원인: {result['root_cause']}")
    print(f"패턴: {result['pattern']}")
    print(f"영향 기기: {', '.join(result['affected_devices'])}")
    print("\n권장 조치:")
    for i, action in enumerate(result["recommended_actions"], 1):
        print(f"  {i}. {action}")
    print(f"\n재발 방지: {result['prevent_recurrence']}")


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    source = f"파일: {file_path}" if file_path else "샘플 로그"

    print(f"로그 분석 시작 ({source})")
    print("-" * 60)

    log = load_log(file_path)
    result = analyze(log)

    print_result(result)

    # JSON 파일로도 저장
    output_file = "analysis_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {output_file}")
