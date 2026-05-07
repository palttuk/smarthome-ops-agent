"""
Phase 2 - Step 2: ChromaDB 벡터 DB 사용
문서를 저장하고 의미 기반으로 검색
실행: python phase2/02_chromadb.py
"""
import chromadb
from dotenv import load_dotenv

load_dotenv()

# 스마트홈 CS 문서 (실제 매뉴얼 대신 샘플)
DOCUMENTS = [
    {
        "id": "doc_001",
        "text": "도어락 배터리 교체 방법: 후면 커버를 열고 AA 배터리 4개를 교체하세요. 배터리 방향에 주의하세요.",
        "metadata": {"category": "도어락", "type": "설치/교체"}
    },
    {
        "id": "doc_002",
        "text": "에어컨 앱 연결 오류 해결: 설정 > 기기 초기화 후 Wi-Fi를 다시 연결하세요. 2.4GHz 대역을 사용하세요.",
        "metadata": {"category": "에어컨", "type": "연결 오류"}
    },
    {
        "id": "doc_003",
        "text": "월패드 화면이 안 켜질 때: 측면 리셋 버튼을 5초간 눌러주세요. 전원 어댑터도 확인하세요.",
        "metadata": {"category": "월패드", "type": "전원 오류"}
    },
    {
        "id": "doc_004",
        "text": "조명 자동화가 안 될 때: 앱 권한 설정에서 위치 권한을 허용하세요. 스케줄을 다시 등록하세요.",
        "metadata": {"category": "조명", "type": "자동화 오류"}
    },
    {
        "id": "doc_005",
        "text": "현관 도어락이 앱에서 제어가 안 될 때: 블루투스와 Wi-Fi를 모두 켜고 앱을 재시작하세요.",
        "metadata": {"category": "도어락", "type": "앱 제어 오류"}
    },
    {
        "id": "doc_006",
        "text": "에어컨이 예약 시간에 안 켜질 때: 앱의 예약 목록을 확인하고 시간대 설정이 올바른지 확인하세요.",
        "metadata": {"category": "에어컨", "type": "자동화 오류"}
    },
    {
        "id": "doc_007",
        "text": "스마트홈 허브 오프라인 상태: 허브 전원을 껐다가 30초 후 다시 켜세요. LED가 파란색이면 정상입니다.",
        "metadata": {"category": "허브", "type": "연결 오류"}
    },
]


def setup_db() -> chromadb.Collection:
    """ChromaDB 초기화 및 문서 저장"""
    client = chromadb.PersistentClient(path="./phase2/chroma_db")

    # 기존 컬렉션 삭제 후 재생성 (실습용)
    try:
        client.delete_collection("smarthome_docs")
    except Exception:
        pass

    collection = client.create_collection(
        name="smarthome_docs",
        metadata={"hnsw:space": "cosine"}
    )

    # 문서 저장
    collection.add(
        ids=[doc["id"] for doc in DOCUMENTS],
        documents=[doc["text"] for doc in DOCUMENTS],
        metadatas=[doc["metadata"] for doc in DOCUMENTS],
    )

    print(f"✅ {collection.count()}개 문서 저장 완료\n")
    return collection


def search_demo(collection: chromadb.Collection):
    """다양한 질문으로 검색 테스트"""
    queries = [
        "배터리가 없어요",
        "앱에서 기기가 안 보여요",
        "자동으로 켜지지 않아요",
        "화면이 꺼졌어요",
    ]

    print("=" * 60)
    print("의미 기반 검색 데모")
    print("=" * 60)

    for query in queries:
        results = collection.query(
            query_texts=[query],
            n_results=2,
            include=["documents", "metadatas", "distances"]
        )

        print(f"\n🔍 질문: '{query}'")
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            similarity = 1 - dist
            print(f"  [{i+1}] 유사도 {similarity:.2f} | {meta['category']} - {meta['type']}")
            print(f"       {doc[:50]}...")


if __name__ == "__main__":
    print("ChromaDB 벡터 DB 실습\n")
    collection = setup_db()
    search_demo(collection)
    print("\n💡 '배터리가 없어요' → '도어락 배터리 교체 방법' 문서를 찾아냄")
    print("   키워드가 달라도 의미가 비슷하면 검색됩니다")
