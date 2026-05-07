"""
Phase 2 - Step 3: 완성된 RAG 체인
검색 → Claude가 답변 생성까지 전체 파이프라인
실행: python phase2/03_rag_chain.py
"""
import chromadb
import anthropic
from dotenv import load_dotenv

load_dotenv()

claude = anthropic.Anthropic()
chroma = chromadb.PersistentClient(path="./phase2/chroma_db")


def get_collection():
    """저장된 컬렉션 로드 (02_chromadb.py 먼저 실행 필요)"""
    try:
        return chroma.get_collection("smarthome_docs")
    except Exception:
        print("❌ DB가 없습니다. 먼저 02_chromadb.py를 실행하세요.")
        exit(1)


def retrieve(collection, query: str, k: int = 2) -> list[dict]:
    """벡터 DB에서 관련 문서 검색"""
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    return [
        {
            "text": doc,
            "category": meta["category"],
            "similarity": round(1 - dist, 3)
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )
    ]


def generate(query: str, context_docs: list[dict]) -> str:
    """검색된 문서를 바탕으로 Claude가 답변 생성"""
    context = "\n".join([
        f"[{doc['category']}] {doc['text']}" for doc in context_docs
    ])

    prompt = f"""당신은 스마트홈 고객 지원 전문가입니다.
아래 참고 문서를 바탕으로 고객 질문에 친절하게 답변하세요.
참고 문서에 없는 내용은 "추가 확인이 필요합니다"라고 답하세요.

참고 문서:
{context}

고객 질문: {query}

답변:"""

    response = claude.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def rag(query: str) -> str:
    """RAG 전체 파이프라인: 검색 → 생성"""
    collection = get_collection()

    # 1. 검색
    docs = retrieve(collection, query)

    # 2. 생성
    answer = generate(query, docs)

    return answer, docs


def run_demo():
    print("=" * 60)
    print("RAG 파이프라인 데모")
    print("=" * 60)

    questions = [
        "도어락 배터리가 없어요. 어떻게 교체하나요?",
        "에어컨이 앱에서 안 켜져요",
        "밤 11시에 조명이 자동으로 안 꺼져요",
        "현관 잠금장치가 스마트폰으로 안 열려요",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"❓ 질문: {q}")

        answer, docs = rag(q)

        print(f"\n📚 참고한 문서:")
        for doc in docs:
            print(f"   - [{doc['category']}] 유사도 {doc['similarity']}")

        print(f"\n💬 답변:\n{answer}")


if __name__ == "__main__":
    run_demo()
