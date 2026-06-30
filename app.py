import streamlit as st
import requests
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import get_youtube, extract_video_id, fmt_num, url_sidebar, base_css

st.set_page_config(page_title="YouTube 분석기", page_icon="📊", layout="centered", initial_sidebar_state="expanded")
base_css()

st.markdown("# 📊 YouTube 영상 분석기")
st.markdown("영상 URL을 넣으면 썸네일·댓글·워드클라우드·채널 정보를 분석해드려요.")
st.markdown("---")

url, run = url_sidebar()

if run:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("올바른 YouTube URL을 입력해주세요.")
        st.stop()

    youtube = get_youtube()
    with st.spinner("불러오는 중..."):
        resp = youtube.videos().list(
            part="snippet,statistics", id=video_id
        ).execute()

    if not resp.get("items"):
        st.error("영상을 찾을 수 없어요.")
        st.stop()

    item = resp["items"][0]
    snippet = item["snippet"]
    stats = item["statistics"]
    channel_id = snippet["channelId"]
    title = snippet["title"]
    published = snippet["publishedAt"][:10]
    view_count = stats.get("viewCount", "0")
    like_count = stats.get("likeCount", "0")
    comment_count = stats.get("commentCount", "0")

    # 썸네일 미리보기
    thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    st.image(thumb_url, use_container_width=True)
    st.markdown(f"""
    <div style="font-size:1.25rem;font-weight:700;color:#1e1b4b;margin:12px 0;
                display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
                overflow:hidden;line-height:1.5;">
      {title}
    </div>
    """, unsafe_allow_html=True)

    # 메트릭 카드
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "📅 게시일", published),
        (c2, "👁️ 조회수", fmt_num(view_count)),
        (c3, "👍 좋아요", fmt_num(like_count)),
        (c4, "💬 댓글수", fmt_num(comment_count)),
    ]:
        col.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📺 같은 채널 인기 영상 TOP 3")

    search_resp = youtube.search().list(
        part="snippet", channelId=channel_id,
        order="viewCount", maxResults=6, type="video"
    ).execute()
    others = [v for v in search_resp.get("items", []) if v["id"]["videoId"] != video_id][:3]

    if others:
        vid_ids = ",".join(v["id"]["videoId"] for v in others)
        vs_resp = youtube.videos().list(part="statistics,snippet", id=vid_ids).execute()
        stats_map = {v["id"]: v for v in vs_resp.get("items", [])}

        cols = st.columns(3)
        for col, v in zip(cols, others):
            vid_id = v["id"]["videoId"]
            vs = stats_map.get(vid_id, {})
            vc = vs.get("statistics", {}).get("viewCount", "0")
            vtitle = v["snippet"]["title"]
            thumb = v["snippet"]["thumbnails"]["medium"]["url"]
            with col:
                st.markdown(f"""
                <div class="video-card">
                  <img src="{thumb}" style="width:100%;border-radius:8px;">
                  <div class="video-title">{vtitle[:28]}{"..." if len(vtitle)>28 else ""}</div>
                  <div class="video-views">👁️ {fmt_num(vc)}회</div>
                  <a href="https://www.youtube.com/watch?v={vid_id}" target="_blank"
                     style="color:#a855f7;font-size:0.8rem;">▶ 보러 가기</a>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.info("👈 왼쪽 메뉴에서 썸네일 다운로드, 댓글, 워드클라우드를 따로 볼 수 있어요!")

else:
    st.markdown("""
    <div style="background:#f8f4ff;border:1px solid #e9d5ff;border-radius:16px;padding:28px;text-align:center;">
      <div style="font-size:3rem;">🎬</div>
      <div style="color:#7c3aed;font-weight:700;font-size:1.1rem;margin:12px 0 6px;">
        왼쪽에 YouTube URL을 붙여넣고 분석을 시작하세요
      </div>
      <div style="color:#6b7280;font-size:0.9rem;">
        썸네일 · 좋아요 댓글 · 워드클라우드 · 채널 인기영상
      </div>
    </div>
    """, unsafe_allow_html=True)
