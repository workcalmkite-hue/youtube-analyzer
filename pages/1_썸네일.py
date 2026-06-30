import streamlit as st
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import get_youtube, extract_video_id, url_sidebar, base_css

st.set_page_config(page_title="썸네일", page_icon="🖼️", layout="centered", initial_sidebar_state="expanded")
base_css()

st.markdown("# 🖼️ 썸네일 다운로드")
st.markdown("---")

url, run = url_sidebar("⬇️ 썸네일 불러오기")
if not run:
    run = bool(st.session_state.get("yt_url"))

if run:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("올바른 YouTube URL을 입력해주세요.")
        st.stop()

    qualities = {
        "최고화질 (1280×720)": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        "고화질 (480×360)":    f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        "중간화질 (320×180)":  f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
    }

    with st.sidebar:
        st.markdown("### 🎨 화질 선택")
        quality_label = st.radio("", list(qualities.keys()), label_visibility="collapsed")

    thumb_url = qualities[quality_label]
    resp = requests.get(thumb_url)

    # 최고화질이 없으면 고화질로 fallback
    if resp.status_code != 200 or len(resp.content) < 5000:
        thumb_url = qualities["고화질 (480×360)"]
        resp = requests.get(thumb_url)
        st.warning("최고화질을 지원하지 않아 고화질로 표시해요.")

    st.image(thumb_url, use_container_width=True)

    st.download_button(
        label="⬇️ 썸네일 저장",
        data=resp.content,
        file_name=f"thumbnail_{video_id}.jpg",
        mime="image/jpeg",
        use_container_width=True,
        type="primary"
    )
else:
    st.markdown("""
    <div style="background:#f8f4ff;border:1px solid #e9d5ff;border-radius:16px;
                padding:40px;text-align:center;">
      <div style="font-size:3rem;">🖼️</div>
      <div style="color:#7c3aed;font-weight:700;margin-top:12px;">
        URL을 입력하면 썸네일을 바로 다운로드할 수 있어요
      </div>
    </div>
    """, unsafe_allow_html=True)
