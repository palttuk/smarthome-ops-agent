# SmartHome Ops Agent

스마트홈 장애를 자동 탐지하고 대응하는 AI 에이전트

## 기술 스택

- **AI**: Claude API (Anthropic), LangGraph
- **RAG**: LangChain + ChromaDB
- **통합**: Slack API, Jira API, MCP
- **인프라**: AWS Lambda, S3, SQS
- **언어**: Python 3.11+

## 학습 단계별 구현

| Phase | 주제 | 상태 |
|-------|------|------|
| Phase 1 | LLM API 기초 + Context Engineering | 🚧 진행 중 |
| Phase 2 | RAG 파이프라인 | 예정 |
| Phase 3 | Function Calling & MCP | 예정 |
| Phase 4 | Agentic AI (LangGraph) | 예정 |
| Phase 5 | AWS 배포 | 예정 |

## 실행 방법

```bash
# 가상환경 설정
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env에 ANTHROPIC_API_KEY 입력

# Phase 1 실행
python phase1/01_first_call.py
```

## Phase 1: LLM API 기초

```
phase1/
├── 01_first_call.py          # Claude API 첫 호출
├── 02_multi_turn.py          # 멀티턴 대화
├── 03_streaming.py           # 스트리밍 응답
├── 04_context_engineering.py # Context Engineering 비교 실습
└── 05_log_analyzer.py        # 실습 프로젝트: 로그 분석기
```
