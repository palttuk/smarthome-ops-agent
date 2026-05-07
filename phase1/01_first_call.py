"""
Phase 1 - Step 1: Claude API 첫 번째 호출
실행: python phase1/01_first_call.py
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()


def ask(prompt: str) -> str:
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


if __name__ == "__main__":
    # 직접 테스트해보기
    questions = [
        "스마트홈 기기가 자꾸 오프라인이 됩니다. 가능한 원인 3가지를 알려주세요.",
        "Python과 TypeScript 중 AI 개발에 더 적합한 언어는 무엇인가요? 한 문장으로.",
    ]

    for q in questions:
        print(f"\n질문: {q}")
        print(f"답변: {ask(q)}")
        print("-" * 60)
