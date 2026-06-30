import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import get_youtube, extract_video_id, url_sidebar, base_css, set_matplotlib_korean

st.set_page_config(page_title="감정 분석", page_icon="😊", layout="centered", initial_sidebar_state="expanded")
base_css()
set_matplotlib_korean()

st.markdown("# 😊 댓글 감정 분석")
st.markdown("---")

url, run = url_sidebar("😊 감정 분석")
if not run:
    run = bool(st.session_state.get("yt_url"))

with st.sidebar:
    st.markdown("### ⚙️ 옵션")
    max_comments = st.slider("분석할 댓글 수", 50, 300, 100, step=50)
    show_samples = st.slider("예시 댓글 수", 3, 10, 5)

# ── 감정 키워드 사전
POSITIVE = [
    "좋아", "좋다", "좋은", "최고", "훌륭", "감동", "재미있", "웃기", "멋있", "멋지",
    "예쁘", "사랑", "행복", "기쁘", "즐거", "신나", "대단", "놀라", "완벽", "천재",
    "갓", "레전드", "명작", "힐링", "따뜻", "감사", "응원", "화이팅", "파이팅", "설레",
    "아름다", "귀엽", "흥미롭", "유익", "도움", "웃음", "귀염", "칭찬", "기대돼",
    "대박", "짱", "최애", "꿀잼", "존잼", "ㅋㅋ", "ㅎㅎ", "👍", "❤", "🥰", "😍", "🎉",
]
NEGATIVE = [
    "싫어", "싫다", "별로", "실망", "최악", "지루", "재미없", "졸리", "짜증", "화나",
    "슬프", "우울", "힘들", "불편", "불만", "나쁘", "구리", "후지", "노잼", "억까",
    "논란", "문제", "걱정", "무섭", "끔찍", "역겹", "혐오", "ㅠㅠ", "ㅜㅜ", "😢",
    "😭", "😤", "👎", "아쉽", "실망스", "별로다", "이해못", "공감안",
]

def classify(text):
    t = text.lower()
    pos = sum(1 for w in POSITIVE if w in t)
    neg = sum(1 for w in NEGATIVE if w in t)
    if pos > neg:
        return "긍정"
    elif neg > pos:
        return "부정"
    else:
        return "중립"

def sentiment_score(text):
    t = text.lower()
    return sum(1 for w in POSITIVE if w in t) - sum(1 for w in NEGATIVE if w in t)

if run:
    video_id = extract_video_id(url)
    if not video_id:
        st.error("올바른 YouTube URL을 입력해주세요.")
        st.stop()

    youtube = get_youtube()

    with st.spinner(f"댓글 {max_comments}개 분석 중..."):
        comments = []
        try:
            req = youtube.commentThreads().list(
                part="snippet", videoId=video_id,
                maxResults=min(100, max_comments), textFormat="plainText"
            )
            while req and len(comments) < max_comments:
                resp = req.execute()
                for item in resp.get("items", []):
                    s = item["snippet"]["topLevelComment"]["snippet"]
                    text = s["textDisplay"]
                    comments.append({
                        "text": text,
                        "likes": s["likeCount"],
                        "label": classify(text),
                        "score": sentiment_score(text),
                    })
                req = youtube.commentThreads().list_next(req, resp)
        except Exception:
            pass

    if not comments:
        st.warning("댓글을 불러올 수 없어요.")
        st.stop()

    counts = {"긍정": 0, "부정": 0, "중립": 0}
    for c in comments:
        counts[c["label"]] += 1
    total = len(comments)

    # ── 요약 배지
    dominant = max(counts, key=counts.get)
    emoji_map = {"긍정": "😊", "부정": "😞", "중립": "😐"}
    color_map = {"긍정": "#a855f7", "부정": "#ef4444", "중립": "#6b7280"}
    bg_map    = {"긍정": "#f8f4ff", "부정": "#fff1f2", "중립": "#f9fafb"}

    st.markdown(f"""
    <div style="background:{bg_map[dominant]};border:1px solid {color_map[dominant]}44;
                border-radius:16px;padding:24px;text-align:center;margin-bottom:20px;">
      <div style="font-size:3rem;">{emoji_map[dominant]}</div>
      <div style="font-size:1.2rem;font-weight:700;color:{color_map[dominant]};margin-top:8px;">
        전체적으로 <strong>{dominant}</strong> 반응이 많아요
      </div>
      <div style="color:#6b7280;font-size:0.9rem;margin-top:4px;">{total}개 댓글 분석 결과</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 비율 카드
    c1, c2, c3 = st.columns(3)
    for col, label in zip([c1, c2, c3], ["긍정", "중립", "부정"]):
        cnt = counts[label]
        pct = round(cnt / total * 100, 1)
        col.markdown(f"""
        <div class="metric-card" style="background:{bg_map[label]};border-color:{color_map[label]}44;">
          <div class="metric-label" style="color:{color_map[label]};">{emoji_map[label]} {label}</div>
          <div class="metric-value" style="color:{color_map[label]};">{pct}%</div>
          <div style="color:#9ca3af;font-size:0.8rem;margin-top:4px;">{cnt}개</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # ── 파이 차트
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["긍정", "중립", "부정"]
    sizes  = [counts["긍정"], counts["중립"], counts["부정"]]
    colors = ["#a855f7", "#d1d5db", "#ef4444"]
    explode = (0.05, 0, 0.05)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, explode=explode,
        autopct="%1.1f%%", startangle=90,
        textprops={"fontsize": 12},
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for at in autotexts:
        at.set_fontsize(11)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title("댓글 감정 분포", fontsize=14, fontweight="bold", pad=15)
    ax.axis("equal")
    fig.patch.set_facecolor("#fafafa")
    st.pyplot(fig)
    plt.close()

    st.markdown("---")

    # ── 긍정 댓글 예시
    pos_comments = sorted(
        [c for c in comments if c["label"] == "긍정"],
        key=lambda x: (x["score"], x["likes"]), reverse=True
    )
    neg_comments = sorted(
        [c for c in comments if c["label"] == "부정"],
        key=lambda x: (-x["score"], x["likes"]), reverse=True
    )

    col_p, col_n = st.columns(2)

    with col_p:
        st.markdown(f"### 😊 긍정 댓글 TOP {show_samples}")
        if pos_comments:
            for c in pos_comments[:show_samples]:
                st.markdown(f"""
                <div style="background:#f8f4ff;border-left:4px solid #a855f7;
                            border-radius:0 10px 10px 0;padding:12px 14px;margin:6px 0;">
                  <div style="color:#1e1b4b;font-size:0.9rem;line-height:1.55;">{c['text'][:120]}{"..." if len(c['text'])>120 else ""}</div>
                  <div style="color:#a855f7;font-size:0.78rem;margin-top:4px;">👍 {c['likes']:,}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("긍정 댓글이 감지되지 않았어요.")

    with col_n:
        st.markdown(f"### 😞 부정 댓글 TOP {show_samples}")
        if neg_comments:
            for c in neg_comments[:show_samples]:
                st.markdown(f"""
                <div style="background:#fff1f2;border-left:4px solid #ef4444;
                            border-radius:0 10px 10px 0;padding:12px 14px;margin:6px 0;">
                  <div style="color:#1f2937;font-size:0.9rem;line-height:1.55;">{c['text'][:120]}{"..." if len(c['text'])>120 else ""}</div>
                  <div style="color:#ef4444;font-size:0.78rem;margin-top:4px;">👍 {c['likes']:,}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("부정 댓글이 감지되지 않았어요.")

else:
    st.markdown("""
    <div style="background:#f8f4ff;border:1px solid #e9d5ff;border-radius:16px;
                padding:40px;text-align:center;">
      <div style="font-size:3rem;">😊</div>
      <div style="color:#7c3aed;font-weight:700;margin-top:12px;">
        URL을 입력하면 댓글 감정을 분석해드려요
      </div>
      <div style="color:#6b7280;font-size:0.9rem;margin-top:6px;">
        긍정 · 부정 · 중립 비율 + 대표 댓글 예시
      </div>
    </div>
    """, unsafe_allow_html=True)
