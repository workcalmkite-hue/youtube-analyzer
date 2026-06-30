import re
import os
import streamlit as st
from googleapiclient.discovery import build

def get_youtube():
    api_key = st.secrets.get("YOUTUBE_API_KEY")
    if not api_key:
        st.error("Streamlit Secrets에 YOUTUBE_API_KEY가 설정되지 않았어요.")
        st.stop()
    return build("youtube", "v3", developerKey=api_key)

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

DEFAULT_URL = "https://youtu.be/nxzbcaf9xK4?si=lKXxx68J5LprxWaj"

def url_sidebar(button_label="🔍 분석"):
    with st.sidebar:
        st.markdown("### 🔗 영상 URL 입력")
        default = st.session_state.get("yt_url", DEFAULT_URL)
        url = st.text_input(
            "url", value=default,
            label_visibility="collapsed"
        )
        if url:
            st.session_state["yt_url"] = url
        run = st.button(button_label, use_container_width=True, type="primary")
    return url, run

FONT_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "C:/Windows/Fonts/malgun.ttf",
]

def get_font():
    return next((p for p in FONT_PATHS if os.path.exists(p)), None)

def set_matplotlib_korean():
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    font = get_font()
    if font:
        fm.fontManager.addfont(font)
        prop = fm.FontProperties(fname=font)
        plt.rcParams["font.family"] = prop.get_name()
    plt.rcParams["axes.unicode_minus"] = False

def base_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .metric-card {
        background: #f8f4ff;
        border: 1px solid #e9d5ff;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
    }
    .metric-label { color: #7c3aed; font-size: 0.82rem; font-weight: 600; margin-bottom: 6px; }
    .metric-value { color: #1e1b4b; font-size: 1.3rem; font-weight: 900; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .comment-card {
        background: #fafafa;
        border-left: 4px solid #a855f7;
        border-radius: 0 12px 12px 0;
        padding: 14px 18px;
        margin: 8px 0;
    }
    .comment-author { color: #7c3aed; font-weight: 700; font-size: 0.88rem; }
    .comment-text { color: #1f2937; margin-top: 4px; line-height: 1.6; }
    .comment-meta { color: #9ca3af; font-size: 0.8rem; margin-top: 6px; }
    .video-card {
        background: #f8f4ff;
        border: 1px solid #e9d5ff;
        border-radius: 14px;
        padding: 14px;
        text-align: center;
    }
    .video-title { color: #1e1b4b; font-weight: 700; font-size: 0.9rem; margin: 8px 0 4px; }
    .video-views { color: #7c3aed; font-size: 0.85rem; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)
