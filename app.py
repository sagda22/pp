"""
포트폴리오 백테스터 — Redesigned Edition
- 내부 로직 100% 동일
- 디자인: Dark Finance Terminal (Bloomberg × 토스증권)
"""

import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings, json
from datetime import date, datetime

warnings.filterwarnings("ignore")
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.family"] = "DejaVu Sans"

st.set_page_config(
    page_title="포트폴리오 백테스터",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — Dark Finance Terminal
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=Pretendard:wght@300;400;500;600;700&display=swap');

/* ── 리셋 & 베이스 ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg-base:     #0C0E14;
  --bg-card:     #13161F;
  --bg-elevated: #1A1E2A;
  --bg-input:    #1E2230;
  --bg-hover:    #252A38;

  --border:      #252A38;
  --border-soft: #1E2230;

  --text-primary:   #EDF0F7;
  --text-secondary: #7B8399;
  --text-muted:     #454D66;

  --blue:   #4F8EF7;
  --green:  #00E5A0;
  --red:    #FF5C5C;
  --orange: #FF9F43;
  --purple: #A78BFA;

  --blue-dim:   rgba(79,142,247,0.12);
  --green-dim:  rgba(0,229,160,0.12);
  --red-dim:    rgba(255,92,92,0.12);

  --font-display: 'Syne', sans-serif;
  --font-mono:    'DM Mono', monospace;
  --font-body:    'Pretendard', -apple-system, sans-serif;

  --radius-sm:  8px;
  --radius-md:  12px;
  --radius-lg:  18px;
  --radius-xl:  24px;
}

html, body, .stApp {
  background: var(--bg-base) !important;
  font-family: var(--font-body) !important;
  color: var(--text-primary) !important;
}

/* Streamlit 껍데기 정리 */
.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}
section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── 전체 앱 레이아웃 ── */
.app-shell {
  display: grid;
  grid-template-columns: 360px 1fr;
  grid-template-rows: auto 1fr;
  min-height: 100vh;
  max-width: 1400px;
  margin: 0 auto;
  gap: 0;
}

/* ── 탑 바 ── */
.topbar {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 32px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-base);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}
.topbar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.topbar-icon {
  width: 36px; height: 36px;
  background: var(--blue);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
}
.topbar-title {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary) !important;
  letter-spacing: -0.02em;
}
.topbar-sub {
  font-size: 0.73rem;
  color: var(--text-muted) !important;
  font-family: var(--font-mono);
}
.topbar-badge {
  display: flex; align-items: center; gap: 6px;
  background: var(--green-dim);
  border: 1px solid rgba(0,229,160,0.2);
  border-radius: 20px;
  padding: 6px 14px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--green) !important;
}
.topbar-badge::before {
  content: '';
  width: 6px; height: 6px;
  background: var(--green);
  border-radius: 50%;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ── 섹션 레이블 ── */
.label {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted) !important;
  margin-bottom: 10px;
  margin-top: 24px;
  display: block;
}
.label:first-child { margin-top: 0; }

/* ── 카드 ── */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 12px;
  transition: border-color 0.2s;
}
.card:hover { border-color: var(--bg-hover); }

/* ── 결과 메트릭 카드 ── */
.result-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 24px;
  margin-bottom: 14px;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, border-color 0.2s;
}
.result-card:hover {
  transform: translateY(-2px);
  border-color: var(--blue);
}
.result-card::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 120px; height: 120px;
  border-radius: 50%;
  opacity: 0.04;
  pointer-events: none;
}
.rc-blue::after   { background: var(--blue);   right: -30px; top: -30px; }
.rc-orange::after { background: var(--orange);  right: -30px; top: -30px; }
.rc-green::after  { background: var(--green);   right: -30px; top: -30px; }
.rc-purple::after { background: var(--purple);  right: -30px; top: -30px; }

.result-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-soft);
}
.rc-name {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.rc-blue .rc-name   { color: var(--blue) !important; }
.rc-orange .rc-name { color: var(--orange) !important; }
.rc-green .rc-name  { color: var(--green) !important; }
.rc-purple .rc-name { color: var(--purple) !important; }

.rc-period {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-muted) !important;
  margin-top: 3px;
}
.rc-final-label {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--text-muted) !important;
  text-align: right;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 2px;
}
.rc-final-value {
  font-family: var(--font-mono);
  font-size: 1.55rem;
  font-weight: 500;
  color: var(--text-primary) !important;
  text-align: right;
  letter-spacing: -0.03em;
}

/* 메트릭 그리드 */
.rc-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.rc-item {
  background: var(--bg-base);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
}
.rc-item-label {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  color: var(--text-muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 5px;
}
.rc-item-value {
  font-family: var(--font-mono);
  font-size: 0.92rem;
  font-weight: 500;
  color: var(--text-primary) !important;
}
.rc-item-value.pos { color: var(--green) !important; }
.rc-item-value.neg { color: var(--red)   !important; }
.rc-item-value.warn { color: var(--orange) !important; }

/* 수익금 배지 */
.profit-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 20px;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  font-weight: 500;
  margin-top: 6px;
}
.profit-badge.pos { background: var(--green-dim); color: var(--green) !important; border: 1px solid rgba(0,229,160,0.2); }
.profit-badge.neg { background: var(--red-dim);   color: var(--red)   !important; border: 1px solid rgba(255,92,92,0.2);  }

/* ── 비교 테이블 ── */
.compare-wrap {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 16px;
}
.compare-row {
  display: grid;
  grid-template-columns: 1.4fr 1.1fr 1.1fr 1fr 1fr;
  padding: 13px 20px;
  border-bottom: 1px solid var(--border-soft);
  align-items: center;
  transition: background 0.15s;
}
.compare-row:last-child { border-bottom: none; }
.compare-row:not(.compare-head):hover { background: var(--bg-elevated); }
.compare-head {
  background: var(--bg-base);
  border-bottom: 1px solid var(--border);
}
.compare-head .cc { color: var(--text-muted) !important; font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase; }
.cc {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  font-weight: 400;
  color: var(--text-primary) !important;
  text-align: right;
}
.cc:first-child { text-align: left; font-family: var(--font-display); font-size: 0.85rem; font-weight: 600; }
.cc.pos { color: var(--green) !important; }
.cc.neg { color: var(--red) !important; }
.cc.warn { color: var(--orange) !important; }

/* ── FX 정보 배너 ── */
.fx-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--blue-dim);
  border: 1px solid rgba(79,142,247,0.2);
  border-radius: var(--radius-md);
  padding: 12px 18px;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--blue) !important;
  margin-bottom: 20px;
}
.fx-banner span { color: var(--text-primary) !important; }

/* ── 섹션 제목 ── */
.section-heading {
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-secondary) !important;
  margin: 28px 0 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.section-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

/* ── Streamlit 위젯 리스타일 ── */
/* 전체 텍스트 */
p, span, div, li, label { color: var(--text-primary) !important; }

/* 버튼 */
.stButton > button {
  background: var(--blue) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  font-size: 0.9rem !important;
  letter-spacing: 0.05em !important;
  padding: 0.85rem 0 !important;
  width: 100% !important;
  margin-top: 8px !important;
  box-shadow: 0 0 24px rgba(79,142,247,0.3) !important;
  transition: all 0.2s !important;
  text-transform: uppercase !important;
}
.stButton > button:hover {
  background: #6BA3F9 !important;
  box-shadow: 0 0 36px rgba(79,142,247,0.5) !important;
  transform: translateY(-1px) !important;
}

/* 슬라이더 */
.stSlider > div > div > div { background: var(--blue) !important; }
.stSlider label { font-family: var(--font-mono) !important; font-size: 0.78rem !important; color: var(--text-secondary) !important; }
[data-testid="stSliderThumb"] { background: var(--blue) !important; border: 2px solid #fff !important; }

/* 인풋 */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
  background: var(--bg-input) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.88rem !important;
}
input:focus, textarea:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px rgba(79,142,247,0.15) !important;
  outline: none !important;
}

/* number input 레이블 */
.stNumberInput label, .stTextInput label, .stTextArea label, .stDateInput label {
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  color: var(--text-muted) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}

/* date input */
[data-baseweb="datepicker"] input { font-family: var(--font-mono) !important; }

/* checkbox */
.stCheckbox label span { color: var(--text-secondary) !important; font-size: 0.82rem !important; }
[data-testid="stCheckbox"] svg { fill: var(--blue) !important; }

/* tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-base) !important;
  border-radius: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
  border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: 0 !important;
  font-family: var(--font-mono) !important;
  font-size: 0.78rem !important;
  color: var(--text-muted) !important;
  padding: 10px 20px !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
}
.stTabs [aria-selected="true"] {
  background: transparent !important;
  color: var(--blue) !important;
  border-bottom: 2px solid var(--blue) !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
  padding: 20px !important;
}

/* expander */
details {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  margin-bottom: 12px !important;
}
details summary {
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  font-size: 0.88rem !important;
  padding: 16px 20px !important;
  color: var(--text-primary) !important;
  cursor: pointer;
  letter-spacing: 0.02em;
}
details[open] summary { border-bottom: 1px solid var(--border) !important; }
details > div { padding: 4px 20px 16px !important; }

/* caption / small */
.stCaption, small { color: var(--text-muted) !important; font-family: var(--font-mono) !important; font-size: 0.72rem !important; }

/* alert */
.stAlert {
  background: var(--bg-elevated) !important;
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border) !important;
}
.stAlert p { color: var(--text-secondary) !important; }

/* success */
[data-testid="stAlert"][data-type="success"] {
  background: var(--green-dim) !important;
  border-color: rgba(0,229,160,0.2) !important;
}
[data-testid="stAlert"][data-type="success"] p { color: var(--green) !important; }

/* info */
[data-testid="stAlert"][data-type="info"] {
  background: var(--blue-dim) !important;
  border-color: rgba(79,142,247,0.2) !important;
}
[data-testid="stAlert"][data-type="info"] p { color: var(--blue) !important; }

/* warning */
[data-testid="stAlert"][data-type="warning"] {
  background: rgba(255,159,67,0.08) !important;
  border-color: rgba(255,159,67,0.2) !important;
}
[data-testid="stAlert"][data-type="warning"] p { color: var(--orange) !important; }

/* error */
[data-testid="stAlert"][data-type="error"] {
  background: var(--red-dim) !important;
  border-color: rgba(255,92,92,0.2) !important;
}
[data-testid="stAlert"][data-type="error"] p { color: var(--red) !important; }

/* hr */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 24px 0 !important; }

/* dataframe */
.stDataFrame { border-radius: var(--radius-md) !important; border: 1px solid var(--border) !important; }

/* download button */
.stDownloadButton > button {
  background: transparent !important;
  color: var(--blue) !important;
  border: 1px solid var(--blue) !important;
  border-radius: var(--radius-sm) !important;
  font-family: var(--font-mono) !important;
  font-weight: 500 !important;
  font-size: 0.78rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  box-shadow: none !important;
}
.stDownloadButton > button:hover { background: var(--blue-dim) !important; }

/* spinner */
.stSpinner > div { border-top-color: var(--blue) !important; }

/* scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--bg-hover); border-radius: 2px; }

/* 페이지 패딩 */
.main-content {
  padding: 32px;
  max-width: 900px;
}

/* 히스토리 엔트리 */
.hist-entry {
  background: var(--bg-elevated);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-md);
  padding: 14px 18px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.hist-name {
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-primary) !important;
}
.hist-meta {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-muted) !important;
  margin-top: 3px;
}

/* 체크박스 활성 */
[data-testid="stCheckbox"]:has(input:checked) span { color: var(--blue) !important; }

/* 전체 배경 강제 */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
section.main,
.main { background: var(--bg-base) !important; }

/* 위젯 배경 */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stHorizontalBlock"] { background: transparent !important; }

/* 반응형 */
@media (max-width: 900px) {
  .rc-grid { grid-template-columns: repeat(2, 1fr) !important; }
  .compare-row { grid-template-columns: 1fr 1fr 1fr !important; }
  .compare-row .cc:nth-child(4),
  .compare-row .cc:nth-child(5) { display: none; }
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
USER_NAME = "수철"
TICKERS = {
    "금현물": "IAU", "나스닥100": "QQQ",
    "현금(소파)": "UUP", "한국리츠": "088980.KS",
}
IS_USD = {"금현물": True, "나스닥100": True, "현금(소파)": True, "한국리츠": False}
COLORS    = ["#4F8EF7", "#FF9F43", "#00E5A0", "#A78BFA"]
RC_CLS    = ["rc-blue", "rc-orange", "rc-green", "rc-purple"]

if "history" not in st.session_state:
    st.session_state.history = []

# ── 유틸 (원본 동일) ──────────────────────────────────────
def safe_float(v):
    if v is None: return 0.0
    try:
        f = float(v)
        return 0.0 if (np.isnan(f) or np.isinf(f)) else f
    except Exception:
        return 0.0

def fmt(v):
    v = safe_float(v)
    s = "-" if v < 0 else ""
    v = abs(v)
    uk = int(v // 1e8)
    mn = int((v % 1e8) // 1e4)
    if uk > 0 and mn > 0: return f"{s}₩{uk:,}억 {mn:,}만"
    if uk > 0: return f"{s}₩{uk:,}억"
    if mn > 0: return f"{s}₩{mn:,}만"
    return f"{s}₩{int(v):,}"

def fmts(v):
    v = safe_float(v)
    return ("+" if v >= 0 else "") + fmt(v)

def pct_cls(v):
    v = safe_float(v)
    if v > 0: return "pos"
    if v < 0: return "neg"
    return ""

def result_card_html(name, m, idx):
    rc   = RC_CLS[idx % len(RC_CLS)]
    ret  = safe_float(m["ret"])
    fv   = safe_float(m["fv"])
    ti   = safe_float(m["ti"])
    profit  = safe_float(m["profit"])
    cagr    = safe_float(m["cagr"])
    vol     = safe_float(m["vol"])
    sharpe  = safe_float(m["sharpe"])
    mdd     = safe_float(m["mdd"])
    years   = safe_float(m["years"])

    pc = pct_cls(profit)
    cc = pct_cls(cagr)
    sr_cls = "pos" if sharpe >= 1 else ("warn" if sharpe >= 0 else "neg")
    mdd_cls = "warn" if mdd > -20 else "neg"

    sign_ret  = "+" if ret  >= 0 else ""
    sign_cagr = "+" if cagr >= 0 else ""
    sign_prof = "+" if profit >= 0 else ""

    return f"""
<div class="result-card {rc}">
  <div class="result-card-header">
    <div>
      <div class="rc-name">{name}</div>
      <div class="rc-period">{years:.1f}YR BACKTEST</div>
    </div>
    <div>
      <div class="rc-final-label">최종 자산</div>
      <div class="rc-final-value">{fmt(fv)}</div>
      <span class="profit-badge {pc}">{sign_prof}{fmts(profit)}</span>
    </div>
  </div>
  <div class="rc-grid">
    <div class="rc-item">
      <div class="rc-item-label">총 투입금</div>
      <div class="rc-item-value">{fmt(ti)}</div>
    </div>
    <div class="rc-item">
      <div class="rc-item-label">누적 수익률</div>
      <div class="rc-item-value {pc}">{sign_ret}{ret:.2f}%</div>
    </div>
    <div class="rc-item">
      <div class="rc-item-label">CAGR (IRR)</div>
      <div class="rc-item-value {cc}">{sign_cagr}{cagr:.2f}%</div>
    </div>
    <div class="rc-item">
      <div class="rc-item-label">연간 변동성</div>
      <div class="rc-item-value">{vol:.2f}%</div>
    </div>
    <div class="rc-item">
      <div class="rc-item-label">샤프 비율</div>
      <div class="rc-item-value {sr_cls}">{sharpe:.2f}</div>
    </div>
    <div class="rc-item">
      <div class="rc-item-label">최대 낙폭 MDD</div>
      <div class="rc-item-value {mdd_cls}">{mdd:.2f}%</div>
    </div>
  </div>
</div>"""

# ── 데이터 (원본 동일) ────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch(start, end):
    syms = list(TICKERS.values())
    raw = yf.download(syms, start=start, end=end,
                      auto_adjust=False, progress=False)["Close"]
    if isinstance(raw, pd.Series): raw = raw.to_frame(name=syms[0])
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.rename(columns={v: k for k, v in TICKERS.items()}, inplace=True)
    raw.dropna(how="all", inplace=True)
    raw.ffill(inplace=True)
    fx = yf.download("KRW=X", start=start, end=end,
                     auto_adjust=False, progress=False)["Close"]
    if isinstance(fx, pd.DataFrame): fx = fx.squeeze()
    fx = fx.reindex(raw.index).ffill().bfill()
    for n in TICKERS:
        if IS_USD.get(n): raw[n] = raw[n] * fx
    return raw, fx

# ── 스케줄 (원본 동일) ────────────────────────────────────
def schedule(cfg, idx):
    d = {}
    if cfg.get("initial", 0) > 0:
        d[idx[0]] = d.get(idx[0], 0) + cfg["initial"]
    if cfg.get("dca", 0) > 0 and cfg.get("freq"):
        for dt in pd.date_range(idx[0], idx[-1], freq=cfg["freq"]):
            fut = idx[idx >= dt]
            if len(fut): d[fut[0]] = d.get(fut[0], 0) + cfg["dca"]
    for ds, amt in cfg.get("custom", {}).items():
        fut = idx[idx >= pd.Timestamp(ds)]
        if len(fut): d[fut[0]] = d.get(fut[0], 0) + amt
    return pd.Series(d).sort_index() if d else pd.Series(dtype=float)

# ── 백테스트 (원본 동일) ──────────────────────────────────
def backtest(prices, weights, yields, cfg, cost):
    names = list(weights.keys())
    w  = np.array([weights[n] for n in names])
    ya = np.array([yields[n]  for n in names])
    dep   = schedule(cfg, prices.index)
    rebal = set()
    for yr in prices.index.year.unique():
        for mo in [1, 7]:
            mask = (prices.index.year == yr) & (prices.index.month == mo)
            if mask.any(): rebal.add(prices.index[mask][0])
    sh, cash, inv, pv, iv, pm = np.zeros(len(names)), 0., 0., [], [], None
    for dt, rw in prices.iterrows():
        pa = rw[names].values.astype(float)
        pa = np.where(np.isfinite(pa) & (pa > 0), pa, np.nan)
        sp = np.where(np.isfinite(pa) & (pa > 0), pa, 1.)
        if dt.month != pm:
            sh += (sh * np.where(np.isfinite(pa), pa, 0)) * ya / sp
            pm = dt.month
        if len(dep) > 0 and dt in dep.index:
            cash += dep[dt]; inv += dep[dt]
            alloc_w = np.where(np.isfinite(pa), w, 0.)
            s = alloc_w.sum()
            if s > 0: alloc_w /= s
            sh += (cash * alloc_w) / sp; cash = 0.
        if dt in rebal and sh.sum() > 0:
            val = np.where(np.isfinite(pa), sh * pa, 0.)
            cv  = val.sum()
            tc  = np.abs(cv * w - val).sum() * cost
            sh  = ((cv - tc) * w) / sp
        port_val = np.nansum(sh * np.where(np.isfinite(pa), pa, 0.)) + cash
        pv.append(port_val)
        iv.append(inv)
    return pd.Series(pv, index=prices.index), pd.Series(iv, index=prices.index)

# ── 지표 (원본 동일) ──────────────────────────────────────
def metrics(pf, inv):
    pf  = pf.fillna(method="ffill").fillna(0)
    inv = inv.fillna(method="ffill").fillna(0)
    ti = safe_float(inv.iloc[-1])
    fv = safe_float(pf.iloc[-1])
    ret    = (fv - ti) / ti * 100 if ti > 0 else 0.0
    profit = fv - ti
    diff = inv.diff().fillna(0); diff.iloc[0] = inv.iloc[0]
    cf   = (diff[diff > 0] * -1.).copy()
    if pf.index[-1] in cf.index:
        cf[pf.index[-1]] = cf[pf.index[-1]] + fv
    else:
        cf[pf.index[-1]] = fv
    full = pd.Series(0., index=pf.index)
    for d, v in cf.sort_index().items():
        if d in full.index: full[d] += v
    try:
        vals = np.where(np.isfinite(full.values), full.values, 0.)
        irr  = npf.irr(vals)
        cagr = (1 + irr) ** 252 - 1 if (np.isfinite(irr) and irr > -1) else 0.
    except Exception:
        cagr = 0.
    dep_days = set(diff[diff > 0].index)
    prev = pf.shift(1).bfill(); dc = pf.diff().fillna(0)
    twr  = pd.Series(0., index=pf.index)
    for d in pf.index:
        if d not in dep_days and prev[d] > 0:
            twr[d] = dc[d] / prev[d]
    vol = safe_float(twr.std() * np.sqrt(252))
    cagr = safe_float(cagr * 100)
    cummax = pf.cummax()
    with np.errstate(invalid="ignore", divide="ignore"):
        dd = np.where(cummax > 0, (pf - cummax) / cummax * 100, 0.)
    mdd = safe_float(np.nanmin(dd))
    years = (pf.index[-1] - pf.index[0]).days / 365.25
    return dict(
        ti=ti, fv=fv, profit=profit, ret=safe_float(ret),
        cagr=cagr, vol=safe_float(vol * 100) if vol < 1 else safe_float(vol),
        sharpe=safe_float((cagr - 3.5) / (vol * 100) if vol > 0 else 0),
        mdd=safe_float(mdd), years=safe_float(years),
    )

# ── 차트 (다크 테마) ──────────────────────────────────────
def chart(results):
    BG    = "#13161F"
    GRID  = "#1E2230"
    TICK  = "#7B8399"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5.5),
                                    facecolor=BG, dpi=140)
    fig.subplots_adjust(hspace=0.55)

    for ax in (ax1, ax2):
        ax.set_facecolor(BG)
        ax.tick_params(colors=TICK, labelsize=7.5, length=0)
        for sp in ax.spines.values():
            sp.set_edgecolor(GRID); sp.set_linewidth(0.6)
        ax.grid(alpha=1, color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)

    for i, (name, (pf, inv)) in enumerate(results.items()):
        c = COLORS[i % len(COLORS)]
        ax1.plot(pf.index,  pf/1e8,  color=c, lw=2.2, label=name, zorder=3)
        ax1.plot(inv.index, inv/1e8, color=c, lw=1.0, ls=":", alpha=0.45, zorder=2)
        ax1.fill_between(pf.index, pf/1e8, inv/1e8, alpha=0.05, color=c)

    ax1.set_title("포트폴리오 가치  vs  투입금 (점선)",
                  fontsize=8, color=TICK, pad=10, loc="left",
                  fontfamily="DejaVu Sans")
    ax1.set_ylabel("억원", fontsize=7.5, color=TICK)
    leg1 = ax1.legend(facecolor="#1A1E2A", edgecolor=GRID,
                      fontsize=7.5, ncol=len(results),
                      loc="upper left", framealpha=0.9)
    for txt in leg1.get_texts(): txt.set_color(TICK)

    for i, (name, (pf, _)) in enumerate(results.items()):
        c  = COLORS[i % len(COLORS)]
        cm = pf.cummax()
        with np.errstate(invalid="ignore", divide="ignore"):
            dd = np.where(cm > 0, (pf - cm) / cm * 100, 0.)
        dd_s = pd.Series(dd, index=pf.index)
        ax2.fill_between(dd_s.index, dd_s, 0, alpha=0.12, color=c)
        ax2.plot(dd_s.index, dd_s, color=c, lw=1.5, label=name)

    ax2.set_title("낙폭 Drawdown (%)",
                  fontsize=8, color=TICK, pad=10, loc="left",
                  fontfamily="DejaVu Sans")
    ax2.set_ylabel("%", fontsize=7.5, color=TICK)
    leg2 = ax2.legend(facecolor="#1A1E2A", edgecolor=GRID,
                      fontsize=7.5, ncol=len(results), framealpha=0.9)
    for txt in leg2.get_texts(): txt.set_color(TICK)

    fig.patch.set_facecolor(BG)
    plt.tight_layout(pad=2.2)
    return fig

# ════════════════════════════════════════════════════════════
#  메인 UI
# ════════════════════════════════════════════════════════════

# ── 탑바 ──────────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-icon">📊</div>
    <div>
      <div class="topbar-title">Portfolio Backtester</div>
      <div class="topbar-sub">안녕하세요, {USER_NAME}님</div>
    </div>
  </div>
  <div class="topbar-badge">LIVE DATA</div>
</div>
""", unsafe_allow_html=True)

# ── 패딩 래퍼 ─────────────────────────────────────────────
st.markdown('<div style="padding: 28px 32px 0;">', unsafe_allow_html=True)

# ── 설정 Expander ─────────────────────────────────────────
with st.expander("⚙  포트폴리오 설정", expanded=True):

    st.markdown('<span class="label">백테스트 기간</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    start_date = c1.date_input("시작일", value=date(2016,1,1),
                                min_value=date(2010,1,1), max_value=date(2024,1,1),
                                label_visibility="visible")
    end_date   = c2.date_input("종료일", value=date(2025,6,30),
                                min_value=date(2011,1,1), max_value=date(2025,12,31),
                                label_visibility="visible")

    st.markdown('<span class="label">자산 비중 (%)</span>', unsafe_allow_html=True)
    w_g = st.slider("금현물",     0, 100, 25, 5)
    w_n = st.slider("나스닥100",  0, 100, 25, 5)
    w_c = st.slider("현금(소파)", 0, 100, 25, 5)
    w_r = st.slider("한국리츠",   0, 100, 25, 5)
    tw  = w_g + w_n + w_c + w_r
    if tw == 0:
        st.error("비중 합계가 0입니다. 슬라이더를 조정해 주세요.")
        st.stop()
    if tw != 100:
        st.warning(f"합계 {tw}% — 실행 시 자동 정규화됩니다.")
    weights = {k: v/tw for k, v in
               {"금현물": w_g, "나스닥100": w_n,
                "현금(소파)": w_c, "한국리츠": w_r}.items()}

    st.markdown('<span class="label">연간 배당 / 분배금률 (%)</span>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    y_g = cc1.number_input("금현물",     0.0, 20.0, 0.0, 0.1)
    y_n = cc2.number_input("나스닥100",  0.0, 20.0, 3.0, 0.1)
    y_c = cc1.number_input("현금(소파)", 0.0, 20.0, 4.0, 0.1)
    y_r = cc2.number_input("한국리츠",   0.0, 20.0, 6.5, 0.1)
    yields = {
        "금현물":     y_g/100/12,
        "나스닥100":  y_n/100/12,
        "현금(소파)": y_c/100/12,
        "한국리츠":   y_r/100/12,
    }

    st.markdown('<span class="label">리밸런싱 수수료 (%)</span>', unsafe_allow_html=True)
    cost = st.slider("수수료", 0.0, 2.0, 0.5, 0.05) / 100

    run_label = st.text_input("테스트 레이블 (선택)", placeholder="예: 공격형 / 안정형 / 은퇴준비")

# ── 시나리오 탭 ───────────────────────────────────────────
st.markdown('<div class="section-heading">입금 시나리오</div>', unsafe_allow_html=True)
tab_a, tab_b, tab_c, tab_d = st.tabs(["일시납", "월적립", "혼합", "커스텀"])
scenarios = {}

with tab_a:
    st.caption("전체 자금을 첫날 한 번에 투입합니다.")
    en_a  = st.checkbox("시나리오 활성화", value=True, key="en_a")
    ini_a = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             100_000_000, 1_000_000, key="ini_a", format="%d")
    st.caption(f"= {fmt(ini_a)}")
    scenarios["일시납"] = {"enabled": en_a, "initial": ini_a, "dca": 0,
                           "freq": None, "custom": {}}

with tab_b:
    st.caption("매월 일정 금액을 꾸준히 적립합니다.")
    en_b  = st.checkbox("시나리오 활성화", value=True, key="en_b")
    dca_b = st.number_input("월 적립금 (원)", 0, 100_000_000,
                             3_000_000, 500_000, key="dca_b", format="%d")
    st.caption(f"월 {fmt(dca_b)} × 12개월 = 연 {fmt(dca_b*12)}")
    scenarios["월적립"] = {"enabled": en_b, "initial": 0, "dca": dca_b,
                           "freq": "MS", "custom": {}}

with tab_c:
    st.caption("초기 목돈 + 매월 추가 적립합니다.")
    en_c  = st.checkbox("시나리오 활성화", value=True, key="en_c")
    ini_c = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             50_000_000, 1_000_000, key="ini_c", format="%d")
    dca_c = st.number_input("월 적립금 (원)", 0, 100_000_000,
                             2_000_000, 500_000, key="dca_c", format="%d")
    st.caption(f"초기 {fmt(ini_c)} + 월 {fmt(dca_c)}")
    scenarios["혼합"] = {"enabled": en_c, "initial": ini_c, "dca": dca_c,
                         "freq": "MS", "custom": {}}

with tab_d:
    st.caption("특정 시점에 비정기 입금합니다. 형식: YYYY-MM-DD: 금액")
    en_d  = st.checkbox("시나리오 활성화", value=True, key="en_d")
    ini_d = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             30_000_000, 1_000_000, key="ini_d", format="%d")
    ct = st.text_area("입금 일정", (
        "2022-04-01: 10000000\n2022-10-01: 15000000\n"
        "2023-03-01: 10000000\n2023-09-01: 20000000\n2024-01-01: 5000000"
    ), height=130, key="ct")
    cds = {}
    for line in ct.strip().split("\n"):
        try:
            p = line.replace(",","").split(":")
            cds[p[0].strip()] = float(p[1].strip())
        except Exception:
            pass
    tcd = sum(cds.values())
    st.caption(f"합계: {fmt(tcd)} ({len(cds)}건)  |  총 예상 투입: {fmt(ini_d+tcd)}")
    scenarios["커스텀"] = {"enabled": en_d, "initial": ini_d, "dca": 0,
                           "freq": None, "custom": cds}

# ── 실행 버튼 ─────────────────────────────────────────────
run_btn = st.button("▶  백테스트 실행")

if run_btn:
    enabled = {k: v for k, v in scenarios.items() if v.get("enabled")}
    if not enabled:
        st.warning("최소 하나의 시나리오를 활성화해 주세요.")
        st.stop()

    prog = st.empty()
    prog.info("📡  Yahoo Finance에서 데이터 수집 중...")
    try:
        prices, fx = fetch(str(start_date), str(end_date))
        prog.success(f"✅  데이터 수집 완료  —  {len(prices):,} 거래일")
    except Exception as e:
        prog.error(f"❌  데이터 수집 실패: {e}")
        st.stop()

    prog.info("⚙  백테스트 계산 중...")
    results = {}
    for name, cfg in enabled.items():
        try:
            pf, inv = backtest(prices, weights, yields, cfg, cost)
            results[name] = (pf, inv)
        except Exception as e:
            st.warning(f"'{name}' 계산 오류: {e}")

    if not results:
        prog.error("모든 시나리오 계산에 실패했습니다.")
        st.stop()

    prog.success(f"✅  백테스트 완료  —  {len(results)}개 시나리오")

    # FX 배너
    try:
        fx_start = safe_float(fx.iloc[0])
        fx_end   = safe_float(fx.iloc[-1])
        fx_chg   = (fx_end / fx_start - 1) * 100 if fx_start > 0 else 0.
        sign = "+" if fx_chg >= 0 else ""
        st.markdown(f"""
<div class="fx-banner">
  💱 원달러 환율
  <span>{str(start_date)[:7]}  {fx_start:.0f}원</span>
  →
  <span>{str(end_date)[:7]}  {fx_end:.0f}원</span>
  ({sign}{fx_chg:.1f}%)
</div>""", unsafe_allow_html=True)
    except Exception:
        pass

    # 성과 카드
    st.markdown('<div class="section-heading">시나리오별 성과</div>', unsafe_allow_html=True)
    for i, (name, (pf, inv)) in enumerate(results.items()):
        try:
            m = metrics(pf, inv)
            st.markdown(result_card_html(name, m, i), unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"'{name}' 결과 오류: {e}")

    # 비교 테이블
    st.markdown('<div class="section-heading">한눈에 비교</div>', unsafe_allow_html=True)
    header_html = """
<div class="compare-wrap">
  <div class="compare-row compare-head">
    <div class="cc">시나리오</div>
    <div class="cc">투입금</div>
    <div class="cc">최종 자산</div>
    <div class="cc">수익률</div>
    <div class="cc">MDD</div>
  </div>"""
    rows_html = ""
    for i, (name, (pf, inv)) in enumerate(results.items()):
        m   = metrics(pf, inv)
        ret = safe_float(m["ret"])
        mdd = safe_float(m["mdd"])
        rc  = "pos" if ret >= 0 else "neg"
        mc  = "warn" if mdd > -20 else "neg"
        rows_html += f"""
  <div class="compare-row">
    <div class="cc">{name}</div>
    <div class="cc">{fmt(m["ti"])}</div>
    <div class="cc">{fmt(m["fv"])}</div>
    <div class="cc {rc}">{"+" if ret>=0 else ""}{ret:.2f}%</div>
    <div class="cc {mc}">{mdd:.2f}%</div>
  </div>"""
    st.markdown(header_html + rows_html + "</div>", unsafe_allow_html=True)

    # 기록 저장
    label = run_label.strip() if run_label.strip() else f"테스트 #{len(st.session_state.history)+1}"
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "label": label,
        "period": f"{start_date} ~ {end_date}",
        "scenarios": {
            n: {"수익률": f'{safe_float(metrics(pf,inv)["ret"]):+.2f}%',
                "CAGR":   f'{safe_float(metrics(pf,inv)["cagr"]):+.2f}%'}
            for n, (pf, inv) in results.items()
        },
    }
    st.session_state.history.insert(0, entry)

    # 차트
    st.markdown('<div class="section-heading">성과 차트</div>', unsafe_allow_html=True)
    try:
        fig = chart(results)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as e:
        st.warning(f"차트 오류 (수치 결과는 정상): {e}")

    # JSON 다운로드
    try:
        json_out = {}
        for name, (pf, inv) in results.items():
            m    = metrics(pf, inv)
            pf_m = pf.resample("ME").last()
            im_m = inv.resample("ME").last()
            json_out[name] = {
                "metrics":   {k: round(safe_float(v), 4) for k, v in m.items()},
                "dates":     [d.strftime("%Y-%m") for d in pf_m.index],
                "portfolio": [round(safe_float(v)) for v in pf_m.values],
                "invested":  [round(safe_float(v)) for v in im_m.values],
            }
        st.download_button(
            "⬇  결과 JSON 다운로드",
            data=json.dumps(json_out, ensure_ascii=False, indent=2).encode(),
            file_name="backtest_results.json",
            mime="application/json",
        )
    except Exception as e:
        st.warning(f"다운로드 준비 오류: {e}")

# ════════════════════════════════════════════════════════════
#  기록 보관함
# ════════════════════════════════════════════════════════════
st.markdown('<div class="section-heading" style="margin-top:36px;">기록 보관함</div>', unsafe_allow_html=True)

if not st.session_state.history:
    st.caption(f"{USER_NAME}님의 백테스트 기록이 없습니다. 실행 후 자동 저장됩니다.")
else:
    st.caption(f"총 {len(st.session_state.history)}건  ·  앱 재시작 시 초기화")
    for i, e in enumerate(st.session_state.history):
        with st.expander(f"📌  {e['label']}  ·  {e['timestamp']}"):
            st.caption(f"기간: {e['period']}")
            for sc, sm in e["scenarios"].items():
                st.markdown(f"**{sc}** — 수익률 {sm['수익률']} / CAGR {sm['CAGR']}")
            if st.button("삭제", key=f"del_{i}"):
                st.session_state.history.pop(i)
                st.rerun()

st.markdown("---")
st.caption("데이터 출처: Yahoo Finance  ·  IAU · QQQ · UUP → KRW=X 환율 적용  ·  088980.KS 원화 직접  ·  본 결과는 투자 참고용입니다.")
st.markdown('</div>', unsafe_allow_html=True)
