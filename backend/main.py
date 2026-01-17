from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import requests
import os
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()

app = FastAPI()

# =========================
# Step 1: 데이터 저장소
# TODO (Step 2): SQLite로 교체
# =========================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
MOVIES_FILE = DATA_DIR / "movies.json"
REVIEWS_FILE = DATA_DIR / "reviews.json"


def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

movies = load_json(MOVIES_FILE, [])
reviews = load_json(REVIEWS_FILE, [])

movie_id_counter = max([m["id"] for m in movies], default=0) + 1
review_id_counter = max([r["id"] for r in reviews], default=0) + 1

SENTIMENT_API_URL = os.getenv("SENTIMENT_API_URL")

# =========================
# 데이터 모델
# =========================
class Movie(BaseModel):
    title: str
    release_date: str
    director: str
    genre: str
    poster_url: str

class MovieResponse(Movie):
    id: int

class Review(BaseModel):
    movie_id: int
    author: str
    content: str

class ReviewResponse(Review):
    id: int
    sentiment_label: str
    sentiment_score: float

# =========================
# 영화 API
# =========================
@app.post("/movies", response_model=MovieResponse)
def add_movie(movie: Movie):
    global movie_id_counter
    data = movie.dict()
    data["id"] = movie_id_counter
    movie_id_counter += 1
    movies.append(data)
    # TODO (Step 2): JSON 저장 → SQLite로 교체
    save_json(MOVIES_FILE, movies)
    return data

@app.get("/movies", response_model=List[MovieResponse])
def get_movies():
    return movies

# =========================
# 리뷰 API
# =========================
@app.post("/reviews", response_model=ReviewResponse)
def create_review(review: Review):
    global review_id_counter

    # 감성 분석 API 호출
    try:
        sentiment_res = requests.post(
            SENTIMENT_API_URL,
            json={"text": review.content},
            timeout=5
        ).json()
    
        label = sentiment_res.get("label", "neutral")
        score = sentiment_res.get("score", 0.0)
    except Exception:
        label = "오류가 발생하여 감성분석에 실패했습니다."
        score = 0.0

    data = review.dict()
    data["id"] = review_id_counter
    review_id_counter += 1
    data["sentiment_label"] = label
    data["sentiment_score"] = score

    reviews.append(data)
    # TODO (Step 2): JSON 저장 → SQLite로 교체
    save_json(REVIEWS_FILE, reviews)
    return data


@app.get("/reviews", response_model=List[ReviewResponse])
def get_reviews():
    return reviews

@app.get("/movies/{movie_id}/rating")
def get_movie_rating(movie_id: int):
    movie_reviews = [
        r for r in reviews if r["movie_id"] == movie_id
    ]

    if not movie_reviews:
        return {
            "rating": None,   # 리뷰 없음
            "count": 0
        }

    avg_score = sum(r["sentiment_score"] for r in movie_reviews) / len(movie_reviews)
    rating_10 = round(avg_score * 10, 1)

    return {
        "rating": rating_10,
        "count": len(movie_reviews)
    }


# =========================
# TODO (심화)
# - 영화별 리뷰 조회
# - 평균 감성 점수 계산
# =========================