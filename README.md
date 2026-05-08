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
| Phase 1 | LLM API 기초 + Context Engineering | ✅ 완료 |
| Phase 2 | RAG 파이프라인 | ✅ 완료 |
| Phase 3 | Function Calling & MCP | ✅ 완료 |
| Phase 4 | Agentic AI (LangGraph) | ✅ 완료 |
| Phase 5 | AWS Lambda 배포 아키텍처 | ✅ 완료 |

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

## Phase 2: RAG 파이프라인

```
phase2/
├── 01_embedding.py    # 임베딩 & 코사인 유사도
├── 02_chromadb.py     # ChromaDB 벡터 저장소
├── 03_rag_chain.py    # RAG 파이프라인 구현
└── 04_cs_bot.py       # 실습: CS 자동화 봇
```

## Phase 3: Function Calling & MCP

```
phase3/
├── 01_tool_use_basic.py   # Tool Use 기초
├── 02_multi_tool_agent.py # 멀티 도구 에이전트 (Slack/Jira mock)
├── 03_real_slack.py       # 실제 Slack 연동
└── 04_ops_agent.py        # 실습: 운영 자동화 에이전트
```

## Phase 4: Agentic AI (LangGraph)

```
phase4/
├── 01_react_pattern.py      # ReAct 패턴 수동 구현
├── 02_langgraph_basic.py    # LangGraph 기초 (StateGraph)
├── 03_stateful_workflow.py  # 도메인 특화 State & 조건부 분기
└── 04_voc_agent.py          # 실습: VOC 자동 분류 에이전트
```

## Phase 5: AWS Lambda 배포 아키텍처

```
phase5/
├── 01_lambda_function.py  # Lambda 핸들러 (API GW / SQS / Slack)
├── 02_s3_storage.py       # S3 로그/분석결과 저장
├── 03_sqs_events.py       # SQS 이벤트 비동기 처리
├── 04_architecture.py     # End-to-End 로컬 시뮬레이션
└── template.yaml          # AWS SAM 배포 템플릿
```
