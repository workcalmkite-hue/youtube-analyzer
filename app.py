import streamlit as st
from googleapiclient.discovery import build
import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import re
from collections import Counter
import os
from datetime import datetime

st.set_page_config(page_title="YouTube 영상 분석기", page_icon="📊", layout="wide")

st.title("📊 YouTube 영상 분석기")
st.markdown("---")

# ── 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.secrets.get("YOUTUBE_API_KEY")
    if not api_key:
        api_key = st.text_input("YouTube API 키", type="password", placeholder="AIza...")
    url_input = st.text_input("분석할 영상 URL", placeholder="https://www.youtube.com/watch?v=...")
    top_n = st.slider("💬 상위 댓글 개수", 5, 50, 10)
    max_comments = st.slider("☁️ 워드클라우드용 댓글 수", 100, 500, 200, step=100)
    run = st.button("🔍 분석 시작", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("**불용어 추가 설정**")
    extra_stop = st.text_area(
        "제외할 단어 (쉼표 구분)",
        placeholder="예: 진짜,정말,완전",
        height=80
    )

# ── 유틸
def extract_video_id(url):
    for p in [r'[?&]v=([0-9A-Za-z_-]{11})', r'youtu\.be/([0-9A-Za-z_-]{11})']:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def fmt_num(n):
    n = int(n)
    if n >= 100000000:
        return f"{n/100000000:.1f}억"
    if n >= 10000:
        return f"{n/10000:.1f}만"
    return f"{n:,}"

BASE_STOPWORDS = {
    "이","가","을","를","은","는","에","의","도","로","으로","와","과","이고","이라",
    "하다","이다","있다","없다","하고","하는","하면","해서","해요","했어","했는데",
    "그냥","진짜","정말","너무","완전","ㅋㅋ","ㅋㅋㅋ","ㅎㅎ","ㅎㅎㅎ","ㅠㅠ","ㅜㅜ",
    "좋아요","싫어요","댓글","구독","알림","설정","유튜브","영상","동영상",
    "보고","보는","봤는데","봤어","그리고","그런데","그래서","그러면","그래도",
    "에서","에게","부터","까지","보다","처럼","같이","같은","이런","그런","저런",
    "이렇게","저렇게","그렇게","이거","저거","그거","이건","그건","저건",
    "거예요","거에요","같아요","것같아","것같습니다","습니다","입니다","이에요",
    "ㄷㄷ","ㄹㄹ","ㄱㄱ","ㅇㅇ","ㄴㄴ","아","어","오","우","음","음..","ㅏ","ㅓ",
    "선생님","감사합니다","감사해요","수고하셨습니다","수고하세요",
}

def get_stopwords(extra_text):
    extra = {w.strip() for w in extra_text.split(",") if w.strip()} if extra_text else set()
    return BASE_STOPWORDS | extra

FONT_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "C:/Windows/Fonts/malgun.ttf",
]

def get_font():
    return next((p for p in FONT_PATHS if os.path.exists(p)), None)

def get_comments(youtube, video_id, max_count):
    comments = []
    try:
        req = youtube.commentThreads().list(
            part="snippet", videoId=video_id,
            maxResults=min(100, max_count), textFormat="plainText"
        )
        while req and len(comments) < max_count:
            resp = req.execute()
            for item in resp.get("items", []):
                s = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "text": s["textDisplay"],
                    "likes": s["likeCount"],
                    "author": s["authorDisplayName"],
                    "date": s["publishedAt"][:10],
                })
            req = youtube.commentThreads().list_next(req, resp)
    except Exception:
        pass
    return comments

# ── 메인 실행
if run:
    if not api_key:
        st.error("YouTube API 키를 입력해주세요.")
        st.stop()
    if not url_input:
        st.error("YouTube URL을 입력해주세요.")
        st.stop()

    video_id = extract_video_id(url_input)
    if not video_id:
        st.error("올바른 YouTube URL이 아니에요.")
        st.stop()

    youtube = build("youtube", "v3", developerKey=api_key)

    with st.spinner("영상 정보 불러오는 중..."):
        video_resp = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()

    if not video_resp.get("items"):
        st.error("영상을 찾을 수 없어요.")
        st.stop()

    item = video_resp["items"][0]
    snippet = item["snippet"]
    stats = item["statistics"]
    channel_id = snippet["channelId"]
    title = snippet["title"]
    published = snippet["publishedAt"][:10]
    view_count = stats.get("viewCount", "0")
    like_count = stats.get("likeCount", "0")
    comment_count = stats.get("commentCount", "0")

    st.markdown(f"## 🎬 {title}")

    # ── 1. 썸네일
    st.markdown("---")
    st.markdown("### 🖼️ 썸네일")
    thumb_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    thumb_resp = requests.get(thumb_url)
    if thumb_resp.status_code != 200 or len(thumb_resp.content) < 5000:
        thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        thumb_resp = requests.get(thumb_url)

    col_img, col_dl = st.columns([3, 1])
    with col_img:
        st.image(thumb_url, use_container_width=True)
    with col_dl:
        st.download_button(
            label="⬇️ 썸네일 다운로드",
            data=thumb_resp.content,
            file_name=f"thumbnail_{video_id}.jpg",
            mime="image/jpeg",
            use_container_width=True
        )

    # ── 4. 영상 통계 (썸네일 아래 바로)
    st.markdown("---")
    st.markdown("### 📈 영상 정보")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 게시일", published)
    c2.metric("👁️ 조회수", fmt_num(view_count))
    c3.metric("👍 좋아요", fmt_num(like_count))
    c4.metric("💬 댓글수", fmt_num(comment_count))

    # ── 댓글 수집
    st.markdown("---")
    with st.spinner(f"댓글 최대 {max_comments}개 수집 중..."):
        comments = get_comments(youtube, video_id, max_comments)

    if not comments:
        st.warning("댓글을 불러올 수 없어요. (댓글 비활성화 또는 API 오류)")
    else:
        # ── 2. 좋아요 많은 댓글
        st.markdown(f"### 👍 좋아요 TOP {top_n} 댓글")
        sorted_comments = sorted(comments, key=lambda x: x["likes"], reverse=True)
        for i, c in enumerate(sorted_comments[:top_n], 1):
            with st.container():
                st.markdown(f"""
                <div style="background:#f8f4ff;border-left:4px solid #a855f7;border-radius:0 10px 10px 0;
                            padding:12px 16px;margin:6px 0;">
                  <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="color:#7c3aed;font-weight:700;">#{i} {c['author']}</span>
                    <span style="color:#9ca3af;font-size:0.85rem;">👍 {c['likes']:,}  {c['date']}</span>
                  </div>
                  <span style="color:#1e1b4b;">{c['text']}</span>
                </div>
                """, unsafe_allow_html=True)

        # ── 3. 워드클라우드
        st.markdown("---")
        st.markdown("### ☁️ 댓글 워드클라우드")
        stopwords = get_stopwords(extra_stop)
        all_text = " ".join(c["text"] for c in comments)
        words = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}', all_text)
        filtered = [w for w in words if w not in stopwords]
        freq = Counter(filtered)

        if freq:
            font = get_font()
            wc_kwargs = dict(
                width=800, height=400,
                background_color="white",
                max_words=100,
                colormap="RdPu",
            )
            if font:
                wc_kwargs["font_path"] = font
            wc = WordCloud(**wc_kwargs).generate_from_frequencies(freq)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
            plt.close()

            with st.expander("단어 빈도 상위 30개 보기"):
                top_words = freq.most_common(30)
                w_col, f_col = st.columns(2)
                with w_col:
                    st.markdown("**단어**")
                    for w, _ in top_words:
                        st.text(w)
                with f_col:
                    st.markdown("**등장 횟수**")
                    for _, cnt in top_words:
                        st.text(cnt)
        else:
            st.info("워드클라우드를 만들 단어가 부족해요.")

    # ── 5. 채널 인기 영상 TOP 3
    st.markdown("---")
    st.markdown("### 📺 같은 채널 인기 영상 TOP 3")
    with st.spinner("채널 영상 검색 중..."):
        search_resp = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="viewCount",
            maxResults=6,
            type="video"
        ).execute()

    other_videos = [
        v for v in search_resp.get("items", [])
        if v["id"]["videoId"] != video_id
    ][:3]

    if other_videos:
        vid_ids = ",".join(v["id"]["videoId"] for v in other_videos)
        vid_stats = youtube.videos().list(part="statistics,snippet", id=vid_ids).execute()
        stats_map = {v["id"]: v for v in vid_stats.get("items", [])}

        cols = st.columns(3)
        for col, v in zip(cols, other_videos):
            vid_id = v["id"]["videoId"]
            vs = stats_map.get(vid_id, {})
            vc = vs.get("statistics", {}).get("viewCount", "0")
            thumb = v["snippet"]["thumbnails"]["medium"]["url"]
            vtitle = v["snippet"]["title"]
            with col:
                st.image(thumb, use_container_width=True)
                st.markdown(f"**{vtitle[:30]}{'...' if len(vtitle)>30 else ''}**")
                st.caption(f"👁️ {fmt_num(vc)} 회")
                st.markdown(f"[YouTube에서 보기](https://www.youtube.com/watch?v={vid_id})")
    else:
        st.info("채널 영상을 불러올 수 없어요.")

else:
    st.info("👈 왼쪽에 API 키와 YouTube URL을 입력하고 분석 시작 버튼을 눌러보세요!")
    st.markdown("""
    **분석 기능:**
    - 🖼️ 썸네일 보기 + 다운로드
    - 👍 좋아요 많은 댓글 TOP N
    - ☁️ 댓글 워드클라우드 (불용어 제거)
    - 📈 조회수·좋아요·댓글 통계
    - 📺 같은 채널 인기 영상 TOP 3
    """)
