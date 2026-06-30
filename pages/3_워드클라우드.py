import streamlit as st
import re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import get_youtube, extract_video_id, url_sidebar, base_css, get_font

st.set_page_config(page_title="워드클라우드", page_icon="☁️", layout="centered", initial_sidebar_state="expanded")
base_css()

st.markdown("# ☁️ 댓글 워드클라우드")
st.markdown("---")

url, run = url_sidebar("☁️ 워드클라우드 생성")

BASE_STOPWORDS = {
    "이","가","을","를","은","는","에","의","도","로","으로","와","과","이고","이라",
    "하다","이다","있다","없다","하고","하는","하면","해서","해요","했어","했는데",
    "그냥","진짜","정말","너무","완전","ㅋㅋ","ㅋㅋㅋ","ㅎㅎ","ㅎㅎㅎ","ㅠㅠ","ㅜㅜ",
    "좋아요","싫어요","댓글","구독","알림","설정","유튜브","영상","동영상",
    "보고","보는","봤는데","봤어","그리고","그런데","그래서","그러면","그래도",
    "에서","에게","부터","까지","보다","처럼","같이","같은","이런","그런","저런",
    "이렇게","저렇게","그렇게","이거","저거","그거","이건","그건","저건",
    "거예요","거에요","같아요","것같아","것같습니다","습니다","입니다","이에요",
    "ㄷㄷ","ㄹㄹ","ㄱㄱ","ㅇㅇ","ㄴㄴ","아","어","오","우","음",
    "감사합니다","감사해요","수고하셨습니다","수고하세요","선생님",
}

with st.sidebar:
    st.markdown("### ⚙️ 옵션")
    max_comments = st.slider("수집할 댓글 수", 100, 500, 200, step=100)
    extra_stop = st.text_area("제외할 단어 (쉼표 구분)", placeholder="예: 진짜,정말,완전", height=80)
    colormap = st.selectbox("색상 테마", ["RdPu", "Blues", "Greens", "Oranges", "viridis", "plasma"])

if run:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("올바른 YouTube URL을 입력해주세요.")
        st.stop()

    youtube = get_youtube()
    extra = {w.strip() for w in extra_stop.split(",") if w.strip()}
    stopwords = BASE_STOPWORDS | extra

    with st.spinner(f"댓글 {max_comments}개 수집 중..."):
        comments = []
        try:
            req = youtube.commentThreads().list(
                part="snippet", videoId=video_id,
                maxResults=100, textFormat="plainText"
            )
            while req and len(comments) < max_comments:
                resp = req.execute()
                for item in resp.get("items", []):
                    s = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append(s["textDisplay"])
                req = youtube.commentThreads().list_next(req, resp)
        except Exception:
            pass

    if not comments:
        st.warning("댓글을 불러올 수 없어요.")
        st.stop()

    all_text = " ".join(comments)
    words = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}', all_text)
    filtered = [w for w in words if w not in stopwords]
    freq = Counter(filtered)

    if not freq:
        st.info("단어가 부족해요. 불용어를 줄여보세요.")
        st.stop()

    st.markdown(f"**{len(comments)}개 댓글 분석 완료 · 고유 단어 {len(freq)}개**")

    font = get_font()
    wc_kwargs = dict(width=900, height=450, background_color="white", max_words=120, colormap=colormap)
    if font:
        wc_kwargs["font_path"] = font
    wc = WordCloud(**wc_kwargs).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)
    st.pyplot(fig)
    plt.close()

    with st.expander("📊 단어 빈도 TOP 30"):
        top30 = freq.most_common(30)
        cols = st.columns(3)
        for i, (word, cnt) in enumerate(top30):
            cols[i % 3].markdown(f"""
            <div style="background:#f8f4ff;border-radius:8px;padding:8px 12px;
                        margin:4px 0;display:flex;justify-content:space-between;">
              <span style="color:#1e1b4b;font-weight:600;">{word}</span>
              <span style="color:#a855f7;font-weight:700;">{cnt}</span>
            </div>
            """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background:#f8f4ff;border:1px solid #e9d5ff;border-radius:16px;
                padding:40px;text-align:center;">
      <div style="font-size:3rem;">☁️</div>
      <div style="color:#7c3aed;font-weight:700;margin-top:12px;">
        URL을 입력하면 댓글 워드클라우드를 생성해드려요
      </div>
      <div style="color:#6b7280;font-size:0.9rem;margin-top:6px;">
        불필요한 단어는 사이드바에서 제외할 수 있어요
      </div>
    </div>
    """, unsafe_allow_html=True)
