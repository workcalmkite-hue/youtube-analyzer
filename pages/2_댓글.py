import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import get_youtube, extract_video_id, url_sidebar, base_css

st.set_page_config(page_title="댓글", page_icon="💬", layout="centered")
base_css()

st.markdown("# 💬 좋아요 TOP 댓글")
st.markdown("---")

url, run = url_sidebar("💬 댓글 불러오기")

with st.sidebar:
    st.markdown("### ⚙️ 옵션")
    top_n = st.slider("상위 댓글 수", 5, 50, 10)

if run:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("올바른 YouTube URL을 입력해주세요.")
        st.stop()

    youtube = get_youtube()

    with st.spinner("댓글 불러오는 중..."):
        comments = []
        try:
            req = youtube.commentThreads().list(
                part="snippet", videoId=video_id,
                maxResults=100, textFormat="plainText"
            )
            while req and len(comments) < 200:
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

    if not comments:
        st.warning("댓글을 불러올 수 없어요. (댓글 비활성화 또는 API 오류)")
        st.stop()

    sorted_comments = sorted(comments, key=lambda x: x["likes"], reverse=True)
    st.markdown(f"**총 {len(comments)}개 댓글 중 좋아요 TOP {top_n}**")

    for i, c in enumerate(sorted_comments[:top_n], 1):
        st.markdown(f"""
        <div class="comment-card">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span class="comment-author">#{i} {c['author']}</span>
            <span class="comment-meta">👍 {c['likes']:,} · {c['date']}</span>
          </div>
          <div class="comment-text">{c['text']}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background:#f8f4ff;border:1px solid #e9d5ff;border-radius:16px;
                padding:40px;text-align:center;">
      <div style="font-size:3rem;">💬</div>
      <div style="color:#7c3aed;font-weight:700;margin-top:12px;">
        URL을 입력하면 좋아요 많은 댓글을 순서대로 보여드려요
      </div>
    </div>
    """, unsafe_allow_html=True)
