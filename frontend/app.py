import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL") or st.secrets["API_BASE_URL"]

st.title("🎬 영화 리뷰 분석 Lab")

# =========================
# 화면 상태 (상세화면용)
# =========================
if "view" not in st.session_state:
    st.session_state["view"] = "list"   # "list" | "detail"

if "selected_movie" not in st.session_state:
    st.session_state["selected_movie"] = None

# =========================
# 사이드바 UI
# =========================

GENRE_OPTIONS = [
    "액션", "드라마", "코미디", "로맨스", "스릴러",
    "공포", "SF", "판타지", "애니메이션", "다큐멘터리", "기타"
]

# 1. 영화 추가
with st.sidebar.expander("➕ 영화 추가", expanded=False):
    with st.form("add_movie"):
        title = st.text_input("제목")
        release_date = st.text_input("개봉년도")
        director = st.text_input("감독")
        genre = st.multiselect(
                        "장르 (복수 선택 가능)",
                        options=GENRE_OPTIONS
                    )
        poster_url = st.text_input("포스터 URL")
        submitted = st.form_submit_button("저장")

        if submitted:
            requests.post(
                f"{API_BASE_URL}/movies",
                json={
                    "title": title,
                    "release_date": release_date,
                    "director": director,
                    "genre": ", ".join(genre),
                    "poster_url": poster_url
                }
            )
            st.success("영화 추가 완료")

# =========================
# 데이터 로드
# =========================
movies = requests.get(f"{API_BASE_URL}/movies").json()
reviews = requests.get(f"{API_BASE_URL}/reviews").json()

# =========================
# 리뷰 영역 함수
# =========================
def render_review_ui(movie, reviews, API_BASE_URL, mode):
    """
    movie: 선택한 영화(dict)
    reviews: 선택한 영화의 전체 리뷰 리스트
    mode: "view" | "write"
    """

    # --------------------
    # 리뷰 보기
    # --------------------
    if mode == "view":
        movie_reviews = [r for r in reviews if r["movie_id"] == movie["id"]]

        if not movie_reviews:
            st.info("아직 등록된 리뷰가 없습니다.")
        else:
            st.write(f"등록된 리뷰: {len(movie_reviews)}개")
            # 리뷰 최신순으로 보기
            movie_reviews = list(reversed(movie_reviews))
            for r in movie_reviews:
                st.markdown(f"""
                **{r['author']}**  
                {r['content']}  
                AI 분석 결과: `{r['sentiment_label']}` (신뢰도: {r['sentiment_score']*100:.2f}%)
                """)
                st.divider()

    # --------------------
    # 리뷰 쓰기
    # --------------------
    elif mode == "write":
        with st.form(key=f"review_form_{movie['id']}"):
            author = st.text_input("작성자")
            content = st.text_area("리뷰 내용")

            submitted = st.form_submit_button("리뷰 등록")

            if submitted:
                requests.post(
                    f"{API_BASE_URL}/reviews",
                    json={
                        "movie_id": movie["id"],
                        "author": author,
                        "content": content
                    }
                )
                st.session_state["review_mode"] = "view"
                st.rerun()

# =========================
# 평점 함수
# =========================
def fetch_rating(movie_id, api_base_url):
    try:
        res = requests.get(
            f"{api_base_url}/movies/{movie_id}/rating",
            timeout=3
        ).json()
        return res
    except Exception:
        return {
            "rating": None,
            "count": 0
        }

# 종합평점 변수 지정
ratings = {}

for m in movies:
    rating_info = fetch_rating(m["id"], API_BASE_URL)

    if rating_info["rating"] is None:
        ratings[m["id"]] = "-"
    else:
        ratings[m["id"]] = f"{rating_info['rating']} / 10"

# =========================
# 메인 영역 UI
# =========================

# 상세 화면
if st.session_state["view"] == "detail":
    movie = st.session_state["selected_movie"]

    st.button("← 목록으로", on_click=lambda: (
        st.session_state.update({
            "view": "list",
            "selected_movie": None
        })
    ))

    st.subheader(f"🎬 {movie['title']} ({movie['release_date']})")

    col1, col2 = st.columns([1, 3])

    with col1:
        if movie.get("poster_url"):
            st.image(movie["poster_url"], width=200)

    with col2:
        st.write(f"감독: {movie['director']}")
        st.write(f"장르: {movie['genre']}")
        st.write(f"개봉년도: {movie['release_date']}")
        st.write(f"⭐ AI 평점: {ratings[movie['id']]}")

    with st.expander("✍️ 리뷰 쓰기", expanded=False):
        render_review_ui(movie, reviews, API_BASE_URL, "write")

    st.subheader("📖 리뷰 보기")
    render_review_ui(movie, reviews, API_BASE_URL, "view")
  

# 홈 화면
else:
    tab_home, tab_movies = st.tabs(["🏠 홈", "🎬 영화목록"])

    # 홈
    with tab_home:
        st.subheader("🔥 평점 높은 영화 TOP 10")

        # 평점 순 TOP 10
        def with_rating(movie):
            info = fetch_rating(movie["id"], API_BASE_URL)
            return info["rating"] or 0

        top10 = sorted(movies, key=with_rating, reverse=True)[:10]

        # UI
        if not top10:
            st.info("아직 등록된 영화가 없습니다.")
        else:
            for m in top10:
                col1, col2 = st.columns([1, 4])

                with col1:
                    if m.get("poster_url"):
                        st.image(m["poster_url"], width=120)

                with col2:
                    st.markdown(f"### {m['title']} ({m['release_date']})")
                    st.write(f"감독: {m['director']}")
                    st.write(f"장르: {m['genre']}")
                    st.write(f"⭐ **AI 평점: {ratings[m['id']]}**")

                    if st.button("상세보기", key=f"detail_home_{m['id']}"):
                        st.session_state["view"] = "detail"
                        st.session_state["selected_movie"] = m
                        st.rerun()
                 
                st.divider()

    # 영화목록 화면
    with tab_movies:
        st.write(f"🎬 등록된 영화: {len(movies)}개")

        for m in movies:
            col1, col2 = st.columns([4,1])
            with col1:
                st.markdown(
                    f"""
                    <span style="font-size:22px; font-weight:600;">
                        {m['id']}. {m['title']} ({m['release_date']})
                    </span>
                    ⭐ <b>AI 평점: {ratings[m['id']]}</b>
                    """,
                    unsafe_allow_html=True
                )
            with col2:
                if st.button("상세보기", key=f"detail_list_{m['id']}"):
                    st.session_state["view"] = "detail"
                    st.session_state["selected_movie"] = m
                    st.rerun()

#            st.divider()
