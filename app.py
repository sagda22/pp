"""
포트폴리오 백테스터 — 토스 스타일
- AI 리포트: 완전 제거 (API 호출이 Streamlit Cloud에서 timeout 유발)
- 텍스트 결과: 차트보다 먼저, 무조건 출력
- UI: 토스증권 스타일 (흰 배경, 라운드 카드, 깔끔한 타이포)
- 다크모드 충돌 방지: !important 최소화, 배경/글자색 명시
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
import warnings
import json
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

# ── CSS: 다크모드 완전 차단, 토스 스타일 ──────────────────
st.markdown("""
<style>
/* ── 다크모드 완전 차단 ── */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], .main { background-color: #f2f4f6 !important; }
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
    background-color: #ffffff !important;
}
.block-container { padding: 2rem 1.2rem 4rem !important; }

/* ── 폰트·텍스트 전역 ── */
html, body, p, span, label, div, h1, h2, h3, h4, li, td, th,
input, textarea, button, select, [class*="st-"] {
    font-family: -apple-system, "Apple SD Gothic Neo", "Noto Sans KR",
                 "Malgun Gothic", sans-serif !important;
    color: #191f28 !important;
}

/* ── 타이포 ── */
h1 { font-size: 1.45rem !important; font-weight: 800 !important;
     letter-spacing: -0.03em !important; }
h2 { font-size: 1.05rem !important; font-weight: 700 !important;
     padding-bottom: 10px !important; margin-top: 2.2rem !important;
     border-bottom: 1px solid #e8eaed !important; }

/* ── 버튼 ── */
.stButton > button {
    background: #3182f6 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.72rem 0 !important;
    width: 100% !important;
    box-shadow: 0 2px 8px rgba(49,130,246,0.22) !important;
}
.stButton > button:hover { background: #1b64da !important; }

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1.5px solid #e8eaed !important; gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.9rem !important; font-weight: 500 !important;
    color: #8b95a1 !important; padding: 10px 20px !important;
    background: transparent !important;
    border-bottom: 2.5px solid transparent !important; margin-bottom: -1.5px !important;
}
.stTabs [aria-selected="true"] {
    color: #191f28 !important; font-weight: 700 !important;
    border-bottom: 2.5px solid #3182f6 !important;
}

/* ── 입력 ── */
input, textarea, .stNumberInput input, .stTextInput input, .stTextArea textarea {
    background: #ffffff !important; color: #191f28 !important;
    border: 1.5px solid #e8eaed !important; border-radius: 10px !important;
}

/* ── expander ── */
details { background: #ffffff !important; border: 1px solid #e8eaed !important;
          border-radius: 12px !important; padding: 4px 14px !important; }

/* ── 알림 ── */
[data-testid="stAlert"] { border-radius: 10px !important; border-left-width: 3px !important; }

/* ── 기타 ── */
hr { border: none !important; border-top: 1px solid #e8eaed !important; margin: 1.8rem 0 !important; }
[data-testid="stCaptionContainer"], .stCaption { color: #8b95a1 !important; font-size: 0.8rem !important; }
.stDataFrame { border-radius: 12px !important; overflow: hidden !important; }
[data-testid="metric-container"] { display: none !important; }
footer, #MainMenu { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  상수 / 세션
# ════════════════════════════════════════════════════════════
USER_NAME = "수철"
DEFAULT_TICKERS = {
    "금현물": "IAU", "나스닥100": "QQQ",
    "현금(소파)": "UUP", "한국리츠": "088980.KS",
}
DEFAULT_IS_USD = {
    "금현물": True, "나스닥100": True, "현금(소파)": True, "한국리츠": False,
}
LABEL_EN = {"일시납": "Lump-sum", "월적립": "Monthly DCA", "혼합": "Hybrid", "커스텀": "Custom"}
COLORS   = ["#3182f6", "#ff6b35", "#00c471", "#8b95a1"]

if "history" not in st.session_state:
    st.session_state.history = []

# ════════════════════════════════════════════════════════════
#  유틸
# ════════════════════════════════════════════════════════════
def fmt_krw(v: float) -> str:
    s = "-" if v < 0 else ""
    v = abs(v)
    uk = int(v // 1e8)
    mn = int((v % 1e8) // 1e4)
    if uk > 0 and mn > 0: return f"{s}₩{uk:,}억 {mn:,}만"
    if uk > 0:             return f"{s}₩{uk:,}억"
    if mn > 0:             return f"{s}₩{mn:,}만"
    return f"{s}₩{int(v):,}"

def fmt_s(v): return ("+" if v >= 0 else "") + fmt_krw(v)

def card(rows_html, title, color="#3182f6"):
    inner = "\n".join(rows_html)
    return f"""
<div style="background:#fff;border-radius:14px;padding:20px 22px;
            border:1px solid #e8eaed;margin-bottom:12px;">
  <div style="font-size:0.72rem;font-weight:800;letter-spacing:0.1em;
              text-transform:uppercase;color:{color};
              border-bottom:2px solid {color};padding-bottom:7px;margin-bottom:14px;">
    {title}
  </div>
  {inner}
</div>"""

def row(k, v, color="#191f28"):
    return f"""<div style="display:flex;justify-content:space-between;
                           padding:7px 0;border-bottom:1px solid #f2f4f6;
                           font-size:0.88rem;">
  <span style="color:#8b95a1;">{k}</span>
  <span style="font-weight:600;color:{color};">{v}</span>
</div>"""

# ════════════════════════════════════════════════════════════
#  데이터 / 엔진
# ════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(tickers, is_usd, start, end):
    syms = list(tickers.values())
    raw  = yf.download(syms, start=start, end=end, auto_adjust=False, progress=False)["Close"]
    if isinstance(raw, pd.Series): raw = raw.to_frame(name=syms[0])
    if isinstance(raw.columns, pd.MultiIndex): raw.columns = raw.columns.get_level_values(0)
    raw.rename(columns={v: k for k, v in tickers.items()}, inplace=True)
    raw.dropna(how="all", inplace=True); raw.ffill(inplace=True)
    fx = yf.download("KRW=X", start=start, end=end, auto_adjust=False, progress=False)["Close"]
    if isinstance(fx, pd.DataFrame): fx = fx.squeeze()
    fx = fx.reindex(raw.index).ffill().bfill()
    for n in tickers:
        if is_usd.get(n): raw[n] = raw[n] * fx
    return raw, fx

def build_schedule(cfg, idx):
    d = {}
    if cfg.get("initial", 0) > 0: d[idx[0]] = d.get(idx[0], 0) + cfg["initial"]
    if cfg.get("dca_amount", 0) > 0 and cfg.get("dca_freq"):
        for dt in pd.date_range(idx[0], idx[-1], freq=cfg["dca_freq"]):
            fut = idx[idx >= dt]
            if len(fut): d[fut[0]] = d.get(fut[0], 0) + cfg["dca_amount"]
    for ds, amt in cfg.get("custom_deposits", {}).items():
        fut = idx[idx >= pd.Timestamp(ds)]
        if len(fut): d[fut[0]] = d.get(fut[0], 0) + amt
    return pd.Series(d).sort_index() if d else pd.Series(dtype=float)

def run_backtest(prices, weights, monthly_yields, cfg, cost):
    names  = list(weights.keys())
    w      = np.array([weights[n] for n in names])
    my_arr = np.array([monthly_yields[n] for n in names])
    dep    = build_schedule(cfg, prices.index)
    rebal  = set()
    for yr in prices.index.year.unique():
        for mo in [1, 7]:
            mask = (prices.index.year == yr) & (prices.index.month == mo)
            if mask.any(): rebal.add(prices.index[mask][0])
    shares, cash, invested, pv, iv, prev_mo = np.zeros(len(names)), 0.0, 0.0, [], [], None
    for dt, rw in prices.iterrows():
        pa = rw[names].values.astype(float)
        sp = np.where(pa > 0, pa, 1.0)
        if dt.month != prev_mo:
            shares += (shares * pa) * my_arr / sp; prev_mo = dt.month
        if len(dep) > 0 and dt in dep.index:
            cash += dep[dt]; invested += dep[dt]
            shares += (cash * w) / sp; cash = 0.0
        if dt in rebal and shares.sum() > 0:
            cv = (shares * pa).sum()
            shares = ((cv - np.abs(cv * w - shares * pa).sum() * cost) * w) / sp
        pv.append((shares * pa).sum() + cash); iv.append(invested)
    return pd.Series(pv, index=prices.index), pd.Series(iv, index=prices.index)

def calc_metrics(pf, inv):
    ti = inv.iloc[-1]; fv = pf.iloc[-1]
    ret = (fv - ti) / ti if ti > 0 else 0
    diff = inv.diff().fillna(0); diff.iloc[0] = inv.iloc[0]
    cf = (diff[diff > 0] * -1.0).copy()
    cf[pf.index[-1]] = cf.get(pf.index[-1], 0) + fv
    full = pd.Series(0.0, index=pf.index)
    for d, v in cf.sort_index().items(): full[d] += v

    # IRR: NaN/inf/극단값 방어
    try:
        vals = full.values
        vals = np.where(np.isfinite(vals), vals, 0.0)
        irr = npf.irr(vals)
        if np.isnan(irr) or np.isinf(irr) or irr < -1:
            irr = 0.0
        cagr = (1 + irr) ** 252 - 1
        if not np.isfinite(cagr): cagr = 0.0
    except Exception:
        cagr = 0.0

    dep_days = set(diff[diff > 0].index)
    prev = pf.shift(1).bfill(); dc = pf.diff().fillna(0)
    twr = pd.Series(0.0, index=pf.index)
    for d in pf.index:
        if d not in dep_days and prev[d] > 0: twr[d] = dc[d] / prev[d]
    vol = twr.std() * np.sqrt(252)
    if not np.isfinite(vol): vol = 0.0
    return dict(
        ti=ti, fv=fv, profit=fv-ti, ret=ret*100,
        cagr=cagr*100, vol=vol*100,
        sharpe=(cagr-0.035)/vol if vol > 0 else 0,
        mdd=((pf-pf.cummax())/pf.cummax()).min()*100,
        years=(pf.index[-1]-pf.index[0]).days/365.25,
    )

# ════════════════════════════════════════════════════════════
#  차트
# ════════════════════════════════════════════════════════════
def make_chart(results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), facecolor="#fff", dpi=110)
    fig.subplots_adjust(hspace=0.55)
    for ax in (ax1, ax2):
        ax.set_facecolor("#fff")
        ax.tick_params(colors="#8b95a1", labelsize=8)
        for sp in ax.spines.values(): sp.set_edgecolor("#e8eaed"); sp.set_linewidth(0.7)
        ax.grid(alpha=0.6, color="#f2f4f6", linewidth=0.6, zorder=0)
    for i, (name, (pf, inv)) in enumerate(results.items()):
        c = COLORS[i % len(COLORS)]; lbl = LABEL_EN.get(name, name)
        ax1.plot(pf.index,  pf  / 1e8, color=c, lw=1.8, label=lbl, zorder=3)
        ax1.plot(inv.index, inv / 1e8, color=c, lw=0.8, ls="--", alpha=0.45, zorder=2)
    ax1.set_title("Portfolio Value vs. Invested  (solid: value / dashed: invested)",
                  fontsize=8.5, color="#8b95a1", pad=8, loc="left")
    ax1.set_ylabel("Billion KRW", fontsize=8, color="#8b95a1")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}B"))
    ax1.legend(facecolor="#fff", edgecolor="#e8eaed", fontsize=8,
               ncol=len(results), loc="upper left", framealpha=1)
    for i, (name, (pf, inv)) in enumerate(results.items()):
        c = COLORS[i % len(COLORS)]; lbl = LABEL_EN.get(name, name)
        dd = (pf - pf.cummax()) / pf.cummax() * 100
        ax2.fill_between(dd.index, dd, 0, alpha=0.1, color=c, zorder=2)
        ax2.plot(dd.index, dd, color=c, lw=1.2, label=lbl, zorder=3)
    ax2.set_title("Drawdown (%)", fontsize=8.5, color="#8b95a1", pad=8, loc="left")
    ax2.set_ylabel("Drawdown (%)", fontsize=8, color="#8b95a1")
    ax2.legend(facecolor="#fff", edgecolor="#e8eaed", fontsize=8, ncol=len(results), framealpha=1)
    fig.patch.set_facecolor("#fff")
    plt.tight_layout(pad=2.0)
    return fig

# ════════════════════════════════════════════════════════════
#  성과 카드
# ════════════════════════════════════════════════════════════
def show_cards(results):
    cols = st.columns(len(results))
    for i, (name, (pf, inv)) in enumerate(results.items()):
        m  = calc_metrics(pf, inv)
        c  = COLORS[i % len(COLORS)]
        pc = "#3182f6" if m["profit"] >= 0 else "#f04452"
        cc = "#3182f6" if m["cagr"]   >= 0 else "#f04452"
        rows = [
            row("총 투입금",   fmt_krw(m["ti"])),
            row("최종 자산",   fmt_krw(m["fv"])),
            row("수익금",      fmt_s(m["profit"]),      pc),
            row("누적 수익률", f'{m["ret"]:+.2f}%',     pc),
            row("CAGR (IRR)",  f'{m["cagr"]:+.2f}%',    cc),
            row("연간 변동성", f'{m["vol"]:.2f}%'),
            row("샤프 비율",   f'{m["sharpe"]:.2f}'),
            row("최대 낙폭",   f'{m["mdd"]:.2f}%',       "#f04452"),
            row("기간",        f'{m["years"]:.1f}년'),
        ]
        with cols[i]:
            st.markdown(card(rows, name, c), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  기록 저장
# ════════════════════════════════════════════════════════════
def save_history(results, label, s, e, weights):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "label": label, "period": f"{s} ~ {e}",
        "weights": {k: f"{v*100:.0f}%" for k, v in weights.items()},
        "scenarios": {},
    }
    for name, (pf, inv) in results.items():
        m = calc_metrics(pf, inv)
        entry["scenarios"][name] = {
            "총 투입금": fmt_krw(m["ti"]), "최종 자산": fmt_krw(m["fv"]),
            "수익률": f'{m["ret"]:+.2f}%', "CAGR": f'{m["cagr"]:+.2f}%',
            "샤프": f'{m["sharpe"]:.2f}', "MDD": f'{m["mdd"]:.2f}%',
        }
    st.session_state.history.insert(0, entry)

# ════════════════════════════════════════════════════════════
#  메인 UI
# ════════════════════════════════════════════════════════════
st.markdown(f"# 포트폴리오 백테스터")
st.markdown(
    f'<p style="color:#8b95a1;font-size:0.9rem;margin-top:-8px;">'
    f'안녕하세요, <b style="color:#191f28;">{USER_NAME}님</b>. '
    f'투자 시나리오를 설정하고 백테스트를 실행해 보세요.</p>',
    unsafe_allow_html=True
)

with st.expander("앱 사용 안내"):
    st.markdown(
        f"**{USER_NAME}님**을 위한 4자산 포트폴리오 시뮬레이터입니다.\n\n"
        "- **금현물(IAU) · 나스닥100(QQQ) · 달러소파(UUP) · 맥쿼리인프라(088980.KS)**\n"
        "- 달러 자산은 실제 원달러 환율 변동을 반영한 **원화 기준 수익률**로 계산합니다\n"
        "- 배당 재투자, 반기 리밸런싱(1·7월), 거래 수수료가 자동 적용됩니다\n\n"
        "**사용법:** 왼쪽 상단 ☰ → 기간·비중 설정 → 시나리오 탭 설정 → 백테스트 실행"
    )

# ── 사이드바 ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### {USER_NAME}님의 설정")
    st.markdown("---")
    st.markdown("**백테스트 기간**")
    c1, c2 = st.columns(2)
    start_date = c1.date_input("시작", value=date(2016,1,1),
                                min_value=date(2010,1,1), max_value=date(2024,1,1),
                                label_visibility="collapsed")
    end_date   = c2.date_input("종료", value=date(2025,6,30),
                                min_value=date(2011,1,1), max_value=date(2025,12,31),
                                label_visibility="collapsed")
    st.caption(f"{start_date} ~ {end_date}")
    st.markdown("---")
    st.markdown("**자산 비중 (%)**")
    w_g = st.slider("금현물",     0, 100, 25, 5)
    w_n = st.slider("나스닥100",  0, 100, 25, 5)
    w_c = st.slider("현금(소파)", 0, 100, 25, 5)
    w_r = st.slider("한국리츠",   0, 100, 25, 5)
    tw  = w_g + w_n + w_c + w_r
    if tw == 0: st.error("비중 합계가 0입니다."); st.stop()
    if tw != 100: st.warning(f"합계 {tw}% → 자동 정규화")
    weights = {k: v/tw for k, v in
               {"금현물": w_g, "나스닥100": w_n, "현금(소파)": w_c, "한국리츠": w_r}.items()}
    st.markdown("---")
    st.markdown("**연간 배당/분배금률 (%)**")
    y_g = st.number_input("금현물",     0.0, 20.0, 0.0, 0.1)
    y_n = st.number_input("나스닥100",  0.0, 20.0, 3.0, 0.1)
    y_c = st.number_input("현금(소파)", 0.0, 20.0, 4.0, 0.1)
    y_r = st.number_input("한국리츠",   0.0, 20.0, 6.5, 0.1)
    monthly_yields = {
        "금현물": y_g/100/12, "나스닥100": y_n/100/12,
        "현금(소파)": y_c/100/12, "한국리츠": y_r/100/12,
    }
    st.markdown("---")
    st.markdown("**리밸런싱 수수료 (%)**")
    cost = st.slider("수수료", 0.0, 2.0, 0.5, 0.05) / 100
    st.markdown("---")
    st.markdown("**테스트 이름** (선택)")
    run_label = st.text_input("이름", placeholder="예: 공격형 포트폴리오",
                               label_visibility="collapsed")

# ── 시나리오 탭 ───────────────────────────────────────────
st.markdown("## 입금 시나리오")
tab_a, tab_b, tab_c, tab_d = st.tabs(["A. 일시납", "B. 월적립", "C. 혼합", "D. 커스텀"])
scenarios = {}

with tab_a:
    st.caption("전체 자금을 첫날 한 번에 투입합니다.")
    en_a  = st.checkbox("활성화", value=True, key="en_a")
    ini_a = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             100_000_000, 1_000_000, key="ini_a", format="%d")
    st.caption(f"= {fmt_krw(ini_a)}")
    scenarios["일시납"] = {"enabled": en_a, "initial": ini_a, "dca_amount": 0, "dca_freq": None}

with tab_b:
    st.caption("매월 일정 금액을 꾸준히 적립합니다.")
    en_b  = st.checkbox("활성화", value=True, key="en_b")
    dca_b = st.number_input("월 적립금 (원)", 0, 100_000_000,
                             3_000_000, 500_000, key="dca_b", format="%d")
    st.caption(f"월 {fmt_krw(dca_b)} × 12 = 연 {fmt_krw(dca_b*12)}")
    scenarios["월적립"] = {"enabled": en_b, "initial": 0, "dca_amount": dca_b, "dca_freq": "MS"}

with tab_c:
    st.caption("초기 목돈 투입 후 매월 추가 적립합니다.")
    en_c  = st.checkbox("활성화", value=True, key="en_c")
    ini_c = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             50_000_000, 1_000_000, key="ini_c", format="%d")
    dca_c = st.number_input("월 적립금 (원)", 0, 100_000_000,
                             2_000_000, 500_000, key="dca_c", format="%d")
    st.caption(f"초기 {fmt_krw(ini_c)} + 월 {fmt_krw(dca_c)}")
    scenarios["혼합"] = {"enabled": en_c, "initial": ini_c, "dca_amount": dca_c, "dca_freq": "MS"}

with tab_d:
    st.caption("특정 시점에 비정기적으로 입금합니다.")
    en_d  = st.checkbox("활성화", value=True, key="en_d")
    ini_d = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             30_000_000, 1_000_000, key="ini_d", format="%d")
    st.caption("날짜: 금액 형식으로 한 줄에 하나씩  예) 2023-03-01: 10000000")
    custom_text = st.text_area("입금 일정", (
        "2022-04-01: 10000000\n2022-10-01: 15000000\n"
        "2023-03-01: 10000000\n2023-09-01: 20000000\n2024-01-01: 5000000"
    ), height=130, key="ct")
    custom_deposits = {}
    for line in custom_text.strip().split("\n"):
        try:
            p = line.replace(",", "").split(":")
            custom_deposits[p[0].strip()] = float(p[1].strip())
        except: pass
    tcd = sum(custom_deposits.values())
    st.caption(f"비정기 합계: {fmt_krw(tcd)} ({len(custom_deposits)}건)  |  총 예상 투입: {fmt_krw(ini_d+tcd)}")
    scenarios["커스텀"] = {
        "enabled": en_d, "initial": ini_d, "dca_amount": 0,
        "dca_freq": None, "custom_deposits": custom_deposits,
    }

# ── 실행 버튼 ─────────────────────────────────────────────
st.markdown("---")
run_btn = st.button("백테스트 실행")

if run_btn:
    enabled = {k: v for k, v in scenarios.items() if v.get("enabled")}
    if not enabled:
        st.warning("하나 이상의 시나리오를 활성화하세요.")
        st.stop()

    # 1단계: 데이터 수집
    with st.spinner("시장 데이터를 불러오는 중..."):
        try:
            prices, fx = fetch_prices(DEFAULT_TICKERS, DEFAULT_IS_USD,
                                       str(start_date), str(end_date))
        except Exception as e:
            st.error(f"데이터 수집 실패: {e}"); st.stop()

    fx_chg = (fx.iloc[-1] / fx.iloc[0] - 1) * 100
    st.info(f"원달러 환율  {str(start_date)[:7]} {fx.iloc[0]:.0f}원 → {str(end_date)[:7]} {fx.iloc[-1]:.0f}원  ({fx_chg:+.1f}%)")

    # 2단계: 계산
    with st.spinner("계산 중..."):
        results = {}
        for name, cfg in enabled.items():
            pf, inv = run_backtest(prices, weights, monthly_yields, cfg, cost)
            results[name] = (pf, inv)

    # ── 결과 출력 (순서 고정, 각 단계 독립) ──────────────

    # 3단계: 성과 카드 (가장 먼저)
    st.markdown("## 시나리오별 성과")
    show_cards(results)

    # 4단계: 비교 테이블
    st.markdown("## 한눈에 비교")
    tbl_rows = []
    for name, (pf, inv) in results.items():
        m = calc_metrics(pf, inv)
        tbl_rows.append({
            "시나리오": name, "총 투입금": fmt_krw(m["ti"]),
            "최종 자산": fmt_krw(m["fv"]), "수익금": fmt_s(m["profit"]),
            "수익률": f'{m["ret"]:+.2f}%', "CAGR": f'{m["cagr"]:+.2f}%',
            "변동성": f'{m["vol"]:.2f}%', "샤프": f'{m["sharpe"]:.2f}',
            "MDD": f'{m["mdd"]:.2f}%',
        })
    st.dataframe(pd.DataFrame(tbl_rows).set_index("시나리오"), use_container_width=True)

    # 5단계: 기록 저장
    label = run_label.strip() if run_label.strip() else f"테스트 {len(st.session_state.history)+1}"
    save_history(results, label, start_date, end_date, weights)
    st.success(f"'{label}' 결과가 기록 보관함에 저장되었습니다.")

    # 6단계: 차트 (실패해도 위 결과에 영향 없음)
    st.markdown("## 성과 차트")
    try:
        fig = make_chart(results)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as e:
        st.warning(f"차트 표시 실패: {e}")

    # 7단계: 다운로드
    json_out = {}
    for name, (pf, inv) in results.items():
        m = calc_metrics(pf, inv)
        pf_m = pf.resample("ME").last()
        im_m = inv.resample("ME").last()
        dd_m = ((pf-pf.cummax())/pf.cummax()).resample("ME").last()
        json_out[name] = {
            "metrics": {k: round(v,2) for k,v in m.items()},
            "dates":     [d.strftime("%Y-%m") for d in pf_m.index],
            "portfolio": [round(v) for v in pf_m.values],
            "invested":  [round(v) for v in im_m.values],
            "drawdown":  [round(v*100,2) for v in dd_m.values],
        }
    st.download_button(
        label="결과 다운로드 (JSON)",
        data=json.dumps(json_out, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="backtest_results.json", mime="application/json",
    )

# ════════════════════════════════════════════════════════════
#  기록 보관함
# ════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 기록 보관함")

if not st.session_state.history:
    st.markdown(
        f'<p style="color:#8b95a1;font-size:0.88rem;">'
        f'{USER_NAME}님의 백테스트 기록이 아직 없습니다. 실행 후 자동 저장됩니다.</p>',
        unsafe_allow_html=True
    )
else:
    st.caption(f"총 {len(st.session_state.history)}건  ·  앱 재시작 시 초기화됩니다")
    all_json = json.dumps(st.session_state.history, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button("전체 기록 다운로드 (JSON)", all_json,
                       file_name="backtest_history.json", mime="application/json")
    for i, entry in enumerate(st.session_state.history):
        with st.expander(f"{entry['label']}  ·  {entry['timestamp']}  ({entry['period']})"):
            st.caption("비중: " + "  /  ".join(f"{k} {v}" for k, v in entry["weights"].items()))
            for sc_name, sc_m in entry["scenarios"].items():
                st.markdown(f"**{sc_name}**")
                c = st.columns(len(sc_m))
                for j, (k, v) in enumerate(sc_m.items()):
                    c[j].markdown(
                        f'<div style="background:#f2f4f6;border-radius:8px;'
                        f'padding:10px 12px;text-align:center;">'
                        f'<div style="font-size:0.7rem;color:#8b95a1;">{k}</div>'
                        f'<div style="font-size:0.95rem;font-weight:700;color:#191f28;">{v}</div>'
                        f'</div>', unsafe_allow_html=True
                    )
            if st.button("삭제", key=f"del_{i}"):
                st.session_state.history.pop(i); st.rerun()

# ── 푸터 ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="color:#8b95a1;font-size:0.78rem;line-height:1.8;">'
    '데이터 출처: Yahoo Finance  ·  달러 자산(IAU·QQQ·UUP): KRW=X 환율 원화 환산  ·  '
    '088980.KS(맥쿼리인프라): 원화 직접  ·  투자 참고 목적이며 수익을 보장하지 않습니다.'
    '</p>',
    unsafe_allow_html=True
)
