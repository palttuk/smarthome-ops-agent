"""
Phase 1 - Step 2: 멀티턴 대화 (대화 이력 유지)
실행: python phase1/02_multi_turn.py
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

SYSTEM = "당신은 스마트홈 기술 전문가입니다. 간결하게 답변하세요."


def chat(history: list[dict], user_input: str) -> tuple[str, list[dict]]:
    history.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=SYSTEM,
        messages=history
    )

    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    return reply, history


def run_chat():
    print("스마트홈 전문가 챗봇 (종료: 'quit')\n")
    history = []

    while True:
        user_input = input("나: ").strip()
        if user_input.lower() in ("quit", "종료", "q"):
            break
        if not user_input:
            continue

        reply, history = chat(history, user_input)
        print(f"AI: {reply}\n")
        print(f"(대화 이력: {len(history) // 2}턴)")


if __name__ == "__main__":
    run_chat()
