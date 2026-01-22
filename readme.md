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
- 리뷰 기반 평점 계산

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
사용모델: nlptown/bert-base-multilingual-uncased-sentiment

### 1) 선정이유:
- 다국어 지원
- 1~5 stars 분류

### 2) Endpoint 요약
| Method | Endpoint            | Input.    | Output         |
| ------ | ------------------- | --------- | -------------- |
| POST   | /analyze            | text      | label, score   |


# 실행코드
uvicorn backend.main:app --reload --port 8000
uvicorn backend.sentiment:app --reload --port 8001

streamlit run ./frontend/app.py