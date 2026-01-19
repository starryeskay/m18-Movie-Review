from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import requests
import os
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()

app = FastAPI()

# =========================
# Step 1: 데이터 저장소
# TODO 시간되면 SQLite로 교체
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
    sentiment_label: Optional[str]
    sentiment_score: float
    rating: Optional[int]

# =========================
# 영화 API
# =========================
@app.post("/movies", response_model=MovieResponse)
def add_movie(movie: Movie):
    global movie_id_counter
    data = movie.model_dump()
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

    rating = None # 기본값: 평점 없음
    
    # 감성 분석 API 호출
    try:
        sentiment_res = requests.post(
            SENTIMENT_API_URL,
            json={"text": review.content},
            timeout=5
        ).json()
    
        label = sentiment_res.get("label")
        score = float(sentiment_res.get("score", 0.0))

        # label → 10점 환산으로 rating 저장 (2배수로 단순 계산)
        # 예: "4 stars" → 8점
        if isinstance(label, str):
            parts = label.split()
            if len(parts) > 0 and parts[0].isdigit():
                stars = int(parts[0])      # 1~5
                rating = stars * 2

    except Exception:
        label = None
        score = 0.0

    data = review.model_dump()
    data["id"] = review_id_counter
    review_id_counter += 1
    data["sentiment_label"] = label
    data["sentiment_score"] = score
    data["rating"] = rating

    reviews.append(data)
    save_json(REVIEWS_FILE, reviews)    # 나중에 SQLite로 교체해보기
    return data


@app.get("/reviews", response_model=List[ReviewResponse])
def get_reviews():
    return reviews

@app.get("/movies/{movie_id}/rating")
def get_movie_rating(movie_id: int):
    movie_reviews = [
        r for r in reviews
        if r["movie_id"] == movie_id and isinstance(r.get("rating"), (int, float))
    ]

    if not movie_reviews:
        return {
            "rating": None,   # 리뷰 없음
            "count": 0
        }

    avg_rating = round(
        sum(r["rating"] for r in movie_reviews) / len(movie_reviews), 1
    )

    return {
        "rating": avg_rating,
        "count": len(movie_reviews)
    }