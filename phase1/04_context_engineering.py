"""
Phase 1 - Step 4: Context Engineering 실습
나쁜 컨텍스트 vs 좋은 컨텍스트 비교 체험
실행: python phase1/04_context_engineering.py
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

# 샘플 로그 (실제와 유사하게)
SAMPLE_LOGS = """
2026-05-07 10:20:01 INFO  gateway    공유기 재부팅 완료
2026-05-07 10:22:55 INFO  device_001 온라인 상태 유지 (신호: -62dBm)
2026-05-07 10:23:01 ERROR device_003 CONNECTION_LOST (신호: -85dBm)
2026-05-07 10:23:05 INFO  device_003 재연결 시도 1/3
2026-05-07 10:23:10 ERROR device_003 CONNECTION_LOST (신호: -87dBm)
2026-05-07 10:23:15 INFO  device_003 재연결 시도 2/3
2026-05-07 10:23:20 ERROR device_003 CONNECTION_LOST (신호: -91dBm)
2026-05-07 10:23:25 WARN  device_003 재연결 실패 - 대기 중
2026-05-07 10:35:00 ERROR device_003 CONNECTION_LOST (신호: -93dBm)
2026-05-07 10:35:05 ERROR device_003 TIMEOUT
2026-05-07 10:50:00 INFO  device_001 온라인 상태 유지 (신호: -63dBm)
2026-05-07 10:50:01 ERROR device_003 CONNECTION_LOST (신호: -95dBm)
"""


def ask(prompt: str) -> str:
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def compare():
    print("=" * 60)
    print("Context Engineering 비교 실험")
    print("=" * 60)

    # ❌ 나쁜 컨텍스트
    bad_prompt = f"이 로그 분석해줘:\n{SAMPLE_LOGS}"

    print("\n[나쁜 컨텍스트]")
    print(f"프롬프트 길이: {len(bad_prompt)}자\n")
    bad_result = ask(bad_prompt)
    print(bad_result)

    print("\n" + "=" * 60)

    # ✅ 좋은 컨텍스트
    good_prompt = f"""
## 분석 요청
목적: device_003 반복 연결 실패 원인 파악

## 기기 정보
- ID: device_003 (거실 에어컨)
- 펌웨어: v2.1.3 (2026-05-01 업데이트)

## 주목할 이벤트 (ERROR/WARN 필터링)
| 시각     | 이벤트           | 신호 강도 |
|---------|-----------------|---------|
| 10:23:01 | CONNECTION_LOST | -85dBm  |
| 10:23:10 | CONNECTION_LOST | -87dBm  |
| 10:23:20 | CONNECTION_LOST | -91dBm  |
| 10:35:00 | CONNECTION_LOST | -93dBm  |
| 10:50:01 | CONNECTION_LOST | -95dBm  |

## 참고 사항
- 10:20에 공유기 재부팅 이력 있음
- 같은 시간대 device_001(-62dBm)은 정상
- 신호 강도가 시간이 지날수록 약해지는 추세

## 요청 형식
JSON으로 답변: {{"root_cause": "...", "confidence": "높음/중간/낮음", "action": "..."}}
"""

    print("\n[좋은 컨텍스트]")
    print(f"프롬프트 길이: {len(good_prompt)}자\n")
    good_result = ask(good_prompt)
    print(good_result)

    print("\n" + "=" * 60)
    print("→ 같은 로그, 다른 컨텍스트 구조 → 답변 품질 차이 확인")


if __name__ == "__main__":
    compare()
