"""
Phase 2 - Step 4: 실습 프로젝트 - 스마트홈 CS 봇
RAG 기반 고객 문의 자동 답변 챗봇
실행: python phase2/04_cs_bot.py
"""
import chromadb
import anthropic
from dotenv import load_dotenv

load_dotenv()

claude = anthropic.Anthropic()
chroma = chromadb.PersistentClient(path="./phase2/chroma_db")

SYSTEM = """당신은 스마트홈 고객 지원 전문가 AI입니다.

규칙:
1. 주어진 참고 문서 안에서만 답변하세요
2. 문서에 없는 내용은 "전문 상담원 연결이 필요합니다 (1588-XXXX)"라고 안내하세요
3. 답변은 간결하게 3줄 이내로 하세요
4. 항상 친절한 어투를 사용하세요"""


def retrieve(query: str, k: int = 2) -> list[str]:
    collection = chroma.get_collection("smarthome_docs")
    results = collection.query(query_texts=[query], n_results=k, include=["documents"])
    return results["documents"][0]


def chat(history: list[dict], user_input: str) -> tuple[str, list[dict]]:
    docs = retrieve(user_input)
    context = "\n".join(docs)

    # 시스템 메시지에 검색된 문서 포함
    system_with_context = f"""{SYSTEM}

현재 질문 관련 참고 문서:
{context}"""

    history.append({"role": "user", "content": user_input})

    response = claude.messages.create(
        model="claude-opus-4-7",
        max_tokens=256,
        system=system_with_context,
        messages=history
    )

    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    return reply, history


def run():
    print("=" * 60)
    print("스마트홈 CS 봇 (RAG 기반)")
    print("종료: 'quit'")
    print("=" * 60)
    print()

    history = []

    while True:
        user_input = input("고객: ").strip()
        if user_input.lower() in ("quit", "종료", "q"):
            print("상담을 종료합니다.")
            break
        if not user_input:
            continue

        reply, history = chat(history, user_input)
        print(f"CS봇: {reply}\n")


if __name__ == "__main__":
    run()
