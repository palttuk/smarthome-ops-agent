"""
Phase 4 - Step 1: ReAct 패턴 직접 구현 (LangGraph 없이)
Reasoning(생각) + Acting(행동) 루프의 원리를 손으로 만들어보기
실행: python phase4/01_react_pattern.py
"""
import anthropic
import json
import re
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

# ── 도구 정의 ──────────────────────────────────────────────────────────
def get_device_status(device_id: str) -> str:
    db = {
        "device_003": "offline | 거실 에어컨 | 마지막 접속: 52분 전 | 에러: 5회",
        "device_001": "online  | 현관 도어락 | 신호: -62dBm | 가동: 3일",
    }
    return db.get(device_id, "not_found")

def get_error_logs(device_id: str) -> str:
    if device_id == "device_003":
        return "10:23 CONNECTION_LOST(-85dBm), 10:35 CONNECTION_LOST(-91dBm), 10:50 TIMEOUT(-95dBm)"
    return "에러 없음"

def restart_device(device_id: str) -> str:
    return f"{device_id} 재시작 신호 전송 완료 (복구 예상: 30초)"

TOOLS = {
    "get_device_status": get_device_status,
    "get_error_logs":    get_error_logs,
    "restart_device":    restart_device,
}

TOOL_DESCRIPTIONS = """
사용 가능한 도구:
- get_device_status(device_id)  : 기기 현재 상태 조회
- get_error_logs(device_id)     : 최근 에러 로그 조회
- restart_device(device_id)     : 기기 원격 재시작

"""

REACT_SYSTEM = TOOL_DESCRIPTIONS + """
다음 형식을 반드시 따르세요:

생각: [현재 상황 분석, 다음에 할 행동 결정]
행동: [도구명]
입력: {"인자명": "값"}

관찰 결과를 받은 후:
생각: [결과 해석, 다음 행동 결정]
행동: [도구명 또는 "완료"]
입력: {"인자명": "값"} 또는 {}

모든 작업이 끝나면:
행동: 완료
최종 답변: [사용자에게 전달할 결론]
"""

def parse_action(text: str) -> tuple[str, dict]:
    """LLM 출력에서 행동과 입력 파싱"""
    action_match = re.search(r"행동:\s*(.+)", text)
    input_match  = re.search(r"입력:\s*(\{.+?\})", text, re.DOTALL)

    action = action_match.group(1).strip() if action_match else "완료"
    try:
        inputs = json.loads(input_match.group(1)) if input_match else {}
    except Exception:
        inputs = {}
    return action, inputs

def run_react(goal: str, max_steps: int = 6) -> str:
    print(f"\n목표: {goal}")
    print("=" * 55)

    messages = [{"role": "user", "content": f"목표: {goal}"}]

    for step in range(1, max_steps + 1):
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            system=REACT_SYSTEM,
            messages=messages
        )
        output = response.content[0].text
        print(f"\n[Step {step}]\n{output}")

        action, inputs = parse_action(output)

        if action == "완료":
            final = re.search(r"최종 답변:\s*(.+)", output, re.DOTALL)
            return final.group(1).strip() if final else output

        # 도구 실행
        if action in TOOLS:
            observation = TOOLS[action](**inputs)
            print(f"\n관찰: {observation}")
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user",      "content": f"관찰: {observation}"})
        else:
            messages.append({"role": "assistant", "content": output})
            messages.append({"role": "user",      "content": "알 수 없는 도구입니다. 다시 시도하세요."})

    return "최대 스텝 초과"

if __name__ == "__main__":
    result = run_react("device_003 상태 확인하고 오프라인이면 로그 보고 재시작해줘")
    print(f"\n{'='*55}\n최종 결과:\n{result}")
