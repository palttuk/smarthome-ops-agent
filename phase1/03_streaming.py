"""
Phase 1 - Step 3: 스트리밍 (실시간 출력)
실행: python phase1/03_streaming.py
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()


def ask_stream(prompt: str) -> str:
    print("AI: ", end="", flush=True)
    full_text = ""

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_text += text

    print()  # 줄바꿈
    return full_text


if __name__ == "__main__":
    prompt = "스마트홈 AI 엔지니어가 되려면 어떤 역량이 필요한지 5가지로 정리해줘."
    print(f"질문: {prompt}\n")
    ask_stream(prompt)
