"""
Phase 2 - Step 1: 임베딩 직접 체험
텍스트 → 숫자 벡터로 변환되는 것을 눈으로 확인
실행: python phase2/01_embedding.py
"""
import anthropic
import json
import math
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()


def get_embedding(text: str) -> list[float]:
    """Claude API로 텍스트 임베딩 생성"""
    # Anthropic은 voyage 모델로 임베딩 제공
    # 직접 구현 대신 간단한 방식으로 체험
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"다음 문장의 핵심 키워드 5개를 쉼표로만 답하세요: {text}"
        }]
    )
    keywords = response.content[0].text.strip()
    return keywords


def cosine_similarity_demo():
    """유사도 개념을 직관적으로 보여주는 데모"""
    # 간단한 벡터로 코사인 유사도 직접 계산
    def dot(v1, v2):
        return sum(a * b for a, b in zip(v1, v2))

    def norm(v):
        return math.sqrt(sum(x**2 for x in v))

    def cosine_sim(v1, v2):
        return dot(v1, v2) / (norm(v1) * norm(v2))

    # 예시: 3차원 벡터로 유사도 개념 설명
    # 실제 임베딩은 수천 차원이지만 원리는 같음
    door_lock_battery   = [0.9, 0.1, 0.8]  # 도어락, 배터리 관련
    entrance_power      = [0.8, 0.2, 0.7]  # 현관, 전원 관련
    aircon_filter       = [0.1, 0.9, 0.2]  # 에어컨, 필터 관련

    sim_1_2 = cosine_sim(door_lock_battery, entrance_power)
    sim_1_3 = cosine_sim(door_lock_battery, aircon_filter)

    print("=" * 60)
    print("코사인 유사도 개념 데모")
    print("=" * 60)
    print(f"\n'도어락 배터리 교체'  vs  '현관 잠금장치 전원'")
    print(f"  → 유사도: {sim_1_2:.3f}  (높음 - 의미가 비슷)")
    print(f"\n'도어락 배터리 교체'  vs  '에어컨 필터 청소'")
    print(f"  → 유사도: {sim_1_3:.3f}  (낮음 - 의미가 다름)")
    print(f"\n💡 RAG는 이 원리로 질문과 가장 유사한 문서를 찾습니다")


def keyword_similarity_demo():
    """Claude로 의미 기반 유사도 체험"""
    print("\n" + "=" * 60)
    print("의미 기반 유사도 체험 (Claude 활용)")
    print("=" * 60)

    pairs = [
        ("도어락 배터리 교체 방법", "현관 잠금장치 전원 교체"),
        ("에어컨 앱 연결 오류", "냉방 기기 Wi-Fi 설정"),
        ("도어락 배터리 교체 방법", "조명 자동화 설정"),
    ]

    for q, doc in pairs:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": f"""다음 두 문장의 의미 유사도를 0~100 숫자 하나로만 답하세요.
문장1: {q}
문장2: {doc}
숫자:"""
            }]
        )
        score = response.content[0].text.strip()
        print(f"\n'{q[:20]}...'")
        print(f"  vs '{doc[:20]}...'")
        print(f"  → 유사도: {score}/100")


if __name__ == "__main__":
    cosine_similarity_demo()
    keyword_similarity_demo()
    print("\n✅ 임베딩 = 텍스트를 숫자 벡터로 변환해 '의미 거리'를 계산하는 것")
