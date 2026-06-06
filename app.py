"""
포트폴리오 백테스터 — Premium Edition
- NaN / inf 완전 방어
- 시중 핀테크 앱 수준 UI (Tosbank / 토스증권 스타일)
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
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ════════════════════════════════════════════════════════════
#  PREMIUM CSS — 토스/카카오페이 스타일
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');

* { box-sizing: border-box; }

html, body, .stApp {
    background: #F0F4F8 !important;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.block-container {
    padding: 2rem 1rem 4rem !important;
    max-width: 680px !important;
    margin: 0 auto !important;
}

/* 사이드바·헤더 완전 숨김 */
section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
#MainMenu, footer, header { display: none !important; }

/* ── 글로벌 텍스트 ── */
h1, h2, h3, h4, p, span, label, div, li { color: #1A1F27 !important; }

/* ── 앱 타이틀 영역 ── */
.app-header {
    background: linear-gradient(135deg, #1A73E8 0%, #0D47A1 100%);
    border-radius: 20px;
    padding: 28px 24px 24px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(26,115,232,0.25);
}
.app-header h1 {
    color: #fff !important;
    font-size: 1.5rem !important;
    font-weight: 800 !important;
    margin: 0 0 4px !important;
}
.app-header p {
    color: rgba(255,255,255,0.78) !important;
    font-size: 0.88rem !important;
    margin: 0 !important;
}

/* ── 섹션 제목 ── */
.section-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6B7684 !important;
    margin: 28px 0 10px !important;
}

/* ── 카드 베이스 ── */
.card {
    background: #fff;
    border-radius: 16px;
    padding: 20px;
    border: 1px solid #E8ECF0;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── 결과 메트릭 카드 ── */
.metric-card {
    background: #fff;
    border-radius: 20px;
    padding: 22px 22px 16px;
    border: 1px solid #E8ECF0;
    margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    overflow: hidden;
    position: relative;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    border-radius: 20px 20px 0 0;
}
.mc-blue::before   { background: #1A73E8; }
.mc-orange::before { background: #FF6B35; }
.mc-green::before  { background: #00C471; }
.mc-gray::before   { background: #8B95A1; }

.metric-badge {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 14px;
}
.badge-blue   { background: #EAF1FD; color: #1A73E8 !important; }
.badge-orange { background: #FFF0EB; color: #FF6B35 !important; }
.badge-green  { background: #E6FAF2; color: #00C471 !important; }
.badge-gray   { background: #F2F4F6; color: #8B95A1 !important; }

.metric-hero {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 16px;
    padding-bottom: 14px;
    border-bottom: 1px solid #F0F4F8;
}
.metric-hero-left {}
.metric-hero-label {
    font-size: 0.78rem;
    color: #8B95A1 !important;
    margin-bottom: 2px;
}
.metric-hero-value {
    font-size: 1.65rem;
    font-weight: 800;
    line-height: 1;
    color: #1A1F27 !important;
}
.metric-hero-right {
    text-align: right;
}
.metric-hero-pct {
    font-size: 1.15rem;
    font-weight: 700;
}
.pos { color: #F04452 !important; }
.neg { color: #1A73E8 !important; }
.neu { color: #1A1F27 !important; }

.metric-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.metric-item {
    background: #F8FAFB;
    border-radius: 10px;
    padding: 10px 12px;
}
.metric-item-label {
    font-size: 0.72rem;
    color: #8B95A1 !important;
    margin-bottom: 3px;
}
.metric-item-value {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1A1F27 !important;
}
.metric-item-value.pos { color: #F04452 !important; }
.metric-item-value.neg { color: #1A73E8 !important; }

/* ── 비교 테이블 ── */
.compare-table {
    background: #fff;
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid #E8ECF0;
    margin-bottom: 16px;
}
.compare-row {
    display: grid;
    grid-template-columns: 1.2fr 1fr 1fr 1fr 1fr;
    padding: 11px 16px;
    border-bottom: 1px solid #F0F4F8;
    align-items: center;
}
.compare-row:last-child { border-bottom: none; }
.compare-header {
    background: #F8FAFB;
    font-size: 0.7rem;
    font-weight: 700;
    color: #8B95A1 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.compare-cell {
    font-size: 0.82rem;
    font-weight: 600;
    color: #1A1F27 !important;
    text-align: right;
}
.compare-cell:first-child {
    text-align: left;
    font-weight: 700;
}

/* ── Streamlit 요소 오버라이드 ── */
.stButton > button {
    background: linear-gradient(135deg, #1A73E8, #0D47A1) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.8rem 0 !important;
    width: 100% !important;
    margin-top: 6px !important;
    box-shadow: 0 4px 16px rgba(26,115,232,0.35) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    box-shadow: 0 6px 20px rgba(26,115,232,0.45) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #E8ECF0 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: #6B7684 !important;
    padding: 8px 12px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #fff !important;
    color: #1A1F27 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }

input, textarea, select {
    background: #F8FAFB !important;
    color: #1A1F27 !important;
    border: 1.5px solid #E8ECF0 !important;
    border-radius: 10px !important;
    font-family: 'Pretendard', sans-serif !important;
}
input:focus, textarea:focus {
    border-color: #1A73E8 !important;
    box-shadow: 0 0 0 3px rgba(26,115,232,0.12) !important;
}

details {
    background: #fff !important;
    border: 1.5px solid #E8ECF0 !important;
    border-radius: 16px !important;
    padding: 2px 0 !important;
}
details summary {
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 14px 18px !important;
    color: #1A1F27 !important;
}

.stSlider > div > div > div { background: #1A73E8 !important; }

/* 정보 박스 */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}

/* dataframe */
.stDataFrame { border-radius: 12px !important; overflow: hidden !important; }

/* 캡션 */
.stCaption, small { color: #8B95A1 !important; font-size: 0.8rem !important; }

/* divider */
hr { border: none !important; border-top: 1px solid #E8ECF0 !important; margin: 20px 0 !important; }

/* checkbox */
.stCheckbox > label { font-size: 0.88rem !important; font-weight: 600 !important; }

/* number input label */
.stNumberInput label { font-size: 0.85rem !important; font-weight: 600 !important; color: #1A1F27 !important; }

/* slider label */
.stSlider label { font-size: 0.85rem !important; font-weight: 600 !important; color: #1A1F27 !important; }

/* expander arrow */
details > summary > span { color: #1A1F27 !important; }

/* download button */
.stDownloadButton > button {
    background: #F0F4F8 !important;
    color: #1A73E8 !important;
    border: 1.5px solid #1A73E8 !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}
.stDownloadButton > button:hover {
    background: #EAF1FD !important;
}

/* spinner */
.stSpinner { color: #1A73E8 !important; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
USER_NAME = "수철"
TICKERS = {
    "금현물": "IAU", "나스닥100": "QQQ",
    "현금(소파)": "UUP", "한국리츠": "088980.KS",
}
IS_USD = {"금현물": True, "나스닥100": True, "현금(소파)": True, "한국리츠": False}
COLORS      = ["#1A73E8", "#FF6B35", "#00C471", "#8B95A1"]
BADGE_CLS   = ["badge-blue", "badge-orange", "badge-green", "badge-gray"]
CARD_CLS    = ["mc-blue",    "mc-orange",    "mc-green",    "mc-gray"]

if "history" not in st.session_state:
    st.session_state.history = []

# ── 유틸 ──────────────────────────────────────────────────
def safe_float(v):
    """NaN / inf → 0"""
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
    return "neu"

def metric_card_html(name, m, idx):
    bc  = BADGE_CLS[idx % len(BADGE_CLS)]
    mc  = CARD_CLS[idx % len(CARD_CLS)]
    ret = safe_float(m["ret"])
    fv  = safe_float(m["fv"])
    ti  = safe_float(m["ti"])
    profit = safe_float(m["profit"])
    cagr   = safe_float(m["cagr"])
    vol    = safe_float(m["vol"])
    sharpe = safe_float(m["sharpe"])
    mdd    = safe_float(m["mdd"])
    years  = safe_float(m["years"])

    pc = pct_cls(profit)
    cc = pct_cls(cagr)
    mc2 = pct_cls(mdd * -1)  # mdd is negative → color red

    sign_ret = "+" if ret >= 0 else ""
    sign_cagr = "+" if cagr >= 0 else ""

    return f"""
<div class="metric-card {mc}">
  <div class="metric-badge {bc}">{name}</div>
  <div class="metric-hero">
    <div class="metric-hero-left">
      <div class="metric-hero-label">최종 자산</div>
      <div class="metric-hero-value">{fmt(fv)}</div>
    </div>
    <div class="metric-hero-right">
      <div class="metric-hero-label">수익금</div>
      <div class="metric-hero-pct {pc}">{fmts(profit)}</div>
    </div>
  </div>
  <div class="metric-grid">
    <div class="metric-item">
      <div class="metric-item-label">총 투입금</div>
      <div class="metric-item-value">{fmt(ti)}</div>
    </div>
    <div class="metric-item">
      <div class="metric-item-label">누적 수익률</div>
      <div class="metric-item-value {pc}">{sign_ret}{ret:.2f}%</div>
    </div>
    <div class="metric-item">
      <div class="metric-item-label">CAGR (IRR)</div>
      <div class="metric-item-value {cc}">{sign_cagr}{cagr:.2f}%</div>
    </div>
    <div class="metric-item">
      <div class="metric-item-label">연간 변동성</div>
      <div class="metric-item-value">{vol:.2f}%</div>
    </div>
    <div class="metric-item">
      <div class="metric-item-label">샤프 비율</div>
      <div class="metric-item-value">{sharpe:.2f}</div>
    </div>
    <div class="metric-item">
      <div class="metric-item-label">최대 낙폭 (MDD)</div>
      <div class="metric-item-value pos">{mdd:.2f}%</div>
    </div>
    <div class="metric-item">
      <div class="metric-item-label">기간</div>
      <div class="metric-item-value">{years:.1f}년</div>
    </div>
  </div>
</div>"""

# ── 데이터 ────────────────────────────────────────────────
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

# ── 스케줄 ────────────────────────────────────────────────
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

# ── 백테스트 ──────────────────────────────────────────────
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
        # 0 또는 NaN 가격 방어
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

# ── 지표 ──────────────────────────────────────────────────
def metrics(pf, inv):
    # NaN 제거 후 계산
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

# ── 차트 ──────────────────────────────────────────────────
def chart(results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5.8),
                                    facecolor="#fff", dpi=130)
    fig.subplots_adjust(hspace=0.60)
    for ax in (ax1, ax2):
        ax.set_facecolor("#FAFBFC")
        ax.tick_params(colors="#8B95A1", labelsize=7.5)
        for sp in ax.spines.values():
            sp.set_edgecolor("#E8ECF0"); sp.set_linewidth(0.6)
        ax.grid(alpha=0.6, color="#F0F4F8", linewidth=0.5)

    for i, (name, (pf, inv)) in enumerate(results.items()):
        c = COLORS[i % len(COLORS)]
        ax1.plot(pf.index,  pf/1e8,  color=c, lw=2.0, label=name)
        ax1.plot(inv.index, inv/1e8, color=c, lw=1.0, ls="--", alpha=0.4)

    ax1.set_title("포트폴리오 가치 vs 투입금  (실선 / 점선)",
                  fontsize=8.5, color="#8B95A1", pad=8, loc="left")
    ax1.set_ylabel("억원", fontsize=7.5, color="#8B95A1")
    ax1.legend(facecolor="#fff", edgecolor="#E8ECF0",
               fontsize=7.5, ncol=len(results), loc="upper left")

    for i, (name, (pf, _)) in enumerate(results.items()):
        c  = COLORS[i % len(COLORS)]
        cm = pf.cummax()
        with np.errstate(invalid="ignore", divide="ignore"):
            dd = np.where(cm > 0, (pf - cm) / cm * 100, 0.)
        dd_s = pd.Series(dd, index=pf.index)
        ax2.fill_between(dd_s.index, dd_s, 0, alpha=0.08, color=c)
        ax2.plot(dd_s.index, dd_s, color=c, lw=1.3, label=name)

    ax2.set_title("낙폭 (Drawdown %)", fontsize=8.5, color="#8B95A1", pad=8, loc="left")
    ax2.set_ylabel("%", fontsize=7.5, color="#8B95A1")
    ax2.legend(facecolor="#fff", edgecolor="#E8ECF0",
               fontsize=7.5, ncol=len(results))

    fig.patch.set_facecolor("#fff")
    plt.tight_layout(pad=2.0)
    return fig

# ════════════════════════════════════════════════════════════
#  메인 UI
# ════════════════════════════════════════════════════════════

# ── 헤더 ──────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
  <h1>📊 포트폴리오 백테스터</h1>
  <p>안녕하세요, <strong>{USER_NAME}님</strong>. 시나리오를 설정하고 10년 수익을 확인하세요.</p>
</div>
""", unsafe_allow_html=True)

# ── 설정 Expander ─────────────────────────────────────────
with st.expander("⚙️  포트폴리오 설정", expanded=True):
    st.markdown('<div class="section-title">백테스트 기간</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    start_date = c1.date_input("시작일", value=date(2016,1,1),
                                min_value=date(2010,1,1), max_value=date(2024,1,1),
                                label_visibility="visible")
    end_date   = c2.date_input("종료일", value=date(2025,6,30),
                                min_value=date(2011,1,1), max_value=date(2025,12,31),
                                label_visibility="visible")

    st.markdown('<div class="section-title">자산 비중 (%)</div>', unsafe_allow_html=True)
    w_g = st.slider("🟡 금현물",     0, 100, 25, 5)
    w_n = st.slider("🔵 나스닥100",  0, 100, 25, 5)
    w_c = st.slider("🟢 현금(소파)", 0, 100, 25, 5)
    w_r = st.slider("🔴 한국리츠",   0, 100, 25, 5)
    tw  = w_g + w_n + w_c + w_r
    if tw == 0:
        st.error("비중 합계가 0입니다. 슬라이더를 조정해 주세요.")
        st.stop()
    if tw != 100:
        st.warning(f"합계 {tw}% → 실행 시 자동 정규화됩니다.")
    weights = {k: v/tw for k, v in
               {"금현물": w_g, "나스닥100": w_n,
                "현금(소파)": w_c, "한국리츠": w_r}.items()}

    st.markdown('<div class="section-title">연간 배당 / 분배금률 (%)</div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-title">리밸런싱 수수료 (%)</div>', unsafe_allow_html=True)
    cost = st.slider("수수료", 0.0, 2.0, 0.5, 0.05) / 100

    run_label = st.text_input("이번 테스트 이름 (선택)",
                               placeholder="예: 공격형 / 안정형 / 은퇴준비")

# ── 시나리오 탭 ───────────────────────────────────────────
st.markdown('<div class="section-title">입금 시나리오</div>', unsafe_allow_html=True)
tab_a, tab_b, tab_c, tab_d = st.tabs(["💰 일시납", "📅 월적립", "🔀 혼합", "✏️ 커스텀"])
scenarios = {}

with tab_a:
    st.caption("전체 자금을 첫날 한 번에 투입합니다.")
    en_a  = st.checkbox("시나리오 활성화", value=True, key="en_a")
    ini_a = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             100_000_000, 1_000_000, key="ini_a", format="%d")
    st.caption(f"= **{fmt(ini_a)}**")
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
    st.caption("특정 시점에 비정기 입금합니다.")
    en_d  = st.checkbox("시나리오 활성화", value=True, key="en_d")
    ini_d = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             30_000_000, 1_000_000, key="ini_d", format="%d")
    st.caption("형식: `YYYY-MM-DD: 금액`  (한 줄에 하나)")
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
st.markdown("")
run_btn = st.button("🚀  백테스트 실행")

if run_btn:
    enabled = {k: v for k, v in scenarios.items() if v.get("enabled")}
    if not enabled:
        st.warning("최소 하나의 시나리오를 활성화해 주세요.")
        st.stop()

    prog = st.empty()

    # 1단계
    prog.info("📡  데이터 수집 중 — Yahoo Finance에 요청하고 있습니다...")
    try:
        prices, fx = fetch(str(start_date), str(end_date))
        prog.success(f"✅  데이터 수집 완료  {len(prices):,}거래일")
    except Exception as e:
        prog.error(f"❌  데이터 수집 실패: {e}")
        st.stop()

    # 2단계
    prog.info("⚙️  백테스트 계산 중...")
    results = {}
    for name, cfg in enabled.items():
        try:
            pf, inv = backtest(prices, weights, yields, cfg, cost)
            results[name] = (pf, inv)
        except Exception as e:
            st.warning(f"'{name}' 시나리오 계산 오류: {e}")

    if not results:
        prog.error("모든 시나리오 계산에 실패했습니다.")
        st.stop()

    prog.success(f"✅  백테스트 완료!  {len(results)}개 시나리오")

    # 환율 안내
    try:
        fx_start = safe_float(fx.iloc[0])
        fx_end   = safe_float(fx.iloc[-1])
        fx_chg   = (fx_end / fx_start - 1) * 100 if fx_start > 0 else 0.
        st.info(
            f"💱  원달러 환율: {str(start_date)[:7]} **{fx_start:.0f}원** → "
            f"{str(end_date)[:7]} **{fx_end:.0f}원** ({fx_chg:+.1f}%)"
        )
    except Exception:
        pass

    # ── 성과 카드 ──
    st.markdown('<div class="section-title">시나리오별 성과</div>', unsafe_allow_html=True)
    for i, (name, (pf, inv)) in enumerate(results.items()):
        try:
            m = metrics(pf, inv)
            st.markdown(metric_card_html(name, m, i), unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"'{name}' 결과 표시 오류: {e}")

    # ── 비교 테이블 ──
    st.markdown('<div class="section-title">한눈에 비교</div>', unsafe_allow_html=True)

    header = '<div class="compare-table"><div class="compare-row compare-header"><div class="compare-cell">시나리오</div><div class="compare-cell">투입금</div><div class="compare-cell">최종자산</div><div class="compare-cell">수익률</div><div class="compare-cell">MDD</div></div>'
    rows_html = ""
    for i, (name, (pf, inv)) in enumerate(results.items()):
        m = metrics(pf, inv)
        ret = safe_float(m["ret"])
        mdd = safe_float(m["mdd"])
        rc = "pos" if ret >= 0 else "neg"
        rows_html += f"""<div class="compare-row">
  <div class="compare-cell">{name}</div>
  <div class="compare-cell">{fmt(m["ti"])}</div>
  <div class="compare-cell">{fmt(m["fv"])}</div>
  <div class="compare-cell {rc}">{"+" if ret>=0 else ""}{ret:.2f}%</div>
  <div class="compare-cell pos">{mdd:.2f}%</div>
</div>"""
    st.markdown(header + rows_html + "</div>", unsafe_allow_html=True)

    # ── 기록 저장 ──
    label = run_label.strip() if run_label.strip() else f"테스트 {len(st.session_state.history)+1}"
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

    # ── 차트 ──
    st.markdown('<div class="section-title">성과 차트</div>', unsafe_allow_html=True)
    try:
        fig = chart(results)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as e:
        st.warning(f"차트 오류 (수치 결과는 정상): {e}")

    # ── JSON 다운로드 ──
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
            "⬇️  결과 JSON 다운로드",
            data=json.dumps(json_out, ensure_ascii=False, indent=2).encode(),
            file_name="backtest_results.json",
            mime="application/json",
        )
    except Exception as e:
        st.warning(f"다운로드 준비 오류: {e}")

# ════════════════════════════════════════════════════════════
#  기록 보관함
# ════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">🗂  기록 보관함</div>', unsafe_allow_html=True)

if not st.session_state.history:
    st.caption(f"{USER_NAME}님의 백테스트 기록이 아직 없습니다. 실행 후 자동 저장됩니다.")
else:
    st.caption(f"총 {len(st.session_state.history)}건 저장됨  ·  앱 재시작 시 초기화")
    for i, e in enumerate(st.session_state.history):
        with st.expander(f"📌 {e['label']}  ·  {e['timestamp']}"):
            st.caption(f"기간: {e['period']}")
            for sc, sm in e["scenarios"].items():
                st.markdown(f"**{sc}** — 수익률 {sm['수익률']} / CAGR {sm['CAGR']}")
            if st.button("🗑  삭제", key=f"del_{i}"):
                st.session_state.history.pop(i)
                st.rerun()

st.markdown("---")
st.caption("데이터 출처: Yahoo Finance  ·  IAU · QQQ · UUP → KRW=X 환율 적용  ·  088980.KS 원화 직접  ·  본 결과는 투자 참고용입니다.")
