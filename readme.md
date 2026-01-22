# 1. 프로젝트 디렉토리 구조 설명
backend/
    ㄴmain.py           메인 비즈니스 API
    ㄴsentiment.py      감성분석 모델 API
frontend/
    ㄴapp.py            Streamlit UI
data/
    ㄴmovies.json       영화 DB
    ㄴreviews.json      리뷰 DB

# 2. 아키텍처 구조
[User]
↓
[Streamlit Frontend]
↓ (HTTP REST)
[Backend API (FastAPI)]
↓ (HTTP REST)
[Sentiment Model API]

# 3. Backend API 설계 (`backend/main.py`)

### 1) 역할 정의
- 영화 CRUD 관리
- 리뷰 등록 및 조회
- 외부 감성 분석 API 연동
- 리뷰 기반 평점 계산 (이진 분류 결과를 신뢰도 반영해 1~5점으로 환산 후 *2)

### 2) 데이터 저장 전략
- JSON 파일 기반
- 서버 시작 시 메모리 로드
- 변경 시 파일 overwrite 저장
- PoC 단계에서는 단순성 우선
- TODO: SQLite / PostgreSQL로 교체 가능 구조

### 3) Endpoint 요약
| Method | Endpoint            | 설명            |
| ------ | ------------------- | ------------- |
| POST   | /movies             | 영화 등록         |
| GET    | /movies             | 영화 목록 조회      |
| POST   | /reviews            | 리뷰 등록 + 감성 분석 |
| GET    | /reviews            | 리뷰 전체 조회      |
| GET    | /movies/{id}/rating | 평균 평점 계산      |

# 4. 감성분석 모델 (`backend/sentiment.py`)
사용모델: 
기존: nlptown/bert-base-multilingual-uncased-sentiment
현재: distilbert-base-uncased-finetuned-sst-2-english

### 1) 모델 선정 이유:
기존 모델
- 다국어 지원
- 1~5 stars 분류
-> Render OOM 이슈로 해당 모델 사용 중단
-> 경량 이진 분류 모델로 교체

### 2) Endpoint 요약
| Method | Endpoint            | Input.    | Output         |
| ------ | ------------------- | --------- | -------------- |
| POST   | /analyze            | text      | label, score   |

# 5. Frontend 설계
- Streamlit 기반 단일 페이지 UI
- 영화 목록 / 상세 화면 상태를 session_state로 관리
- Backend API와 REST 방식으로 통신
- 리뷰 작성 시 실시간으로 감성 분석 결과 및 평점 반영
- 배포 환경에 따라 환경변수(.env / secrets.toml)로 API 주소 분리 관리

1) 메인화면
- 등록된 영화 중 AI 평점 기준 상위 10개 영화를 자동으로 정렬하여 노출
- 사용자는 한눈에 평점이 높은 영화를 확인하고 상세 페이지로 이동 가능

2) 영화 목록 화면
- 현재 시스템에 등록된 전체 영화 목록을 조회
- 각 영화별 AI 평점 요약과 함께 상세보기 진입 버튼 제공

3) 영화 상세 화면
- 선택한 영화의 포스터, 기본 정보(감독·장르·개봉년도) 및 AI 평균 평점 표시
- 리뷰 작성 및 기존 리뷰 조회가 가능한 중심 화면

4) 리뷰 작성 및 분석 결과 화면
- 사용자가 작성한 리뷰를 기반으로 AI 감성 분석 결과(POSITIVE/NEGATIVE)와 신뢰도를 즉시 확인
- 감성 분석 결과는 서비스 정책에 따라 평점 산출에 반영