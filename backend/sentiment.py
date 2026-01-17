from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

app = FastAPI()

# =========================
# 서버 시작 시 모델 1회 로드
# 다국어, 짧은 리뷰에 적합: cardiffnlp/twitter-xlm-roberta-base-sentiment
# 한국어 감성 분석에 적합: beomi/KcELECTRA-base-v2022
# =========================
MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    use_fast=False
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME
)

sentiment_model = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME
)

# =========================
# API 스키마
# =========================
class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    label: str
    score: float

# =========================
# API 엔드포인트
# =========================
@app.post("/analyze", response_model=SentimentResponse)
def analyze_sentiment(req: SentimentRequest):
    result = sentiment_model(req.text)[0]
    return {
        "label": result["label"],
        "score": float(result["score"])
    }