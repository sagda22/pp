"""
포트폴리오 백테스터 - 모바일 최적화 완전판
- 사이드바 완전 제거 (모바일 레이아웃 깨짐 원인)
- 설정을 메인 화면 expander로 이동
- 결과 최우선 출력 + 단계별 진행 표시
- CSS 최소화 (깨짐 방지)
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
    layout="centered",          # wide 대신 centered — 모바일 깨짐 방지
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* 배경 */
.stApp, html, body { background-color: #f5f6f8 !important; }
.block-container { padding: 1.5rem 1rem 3rem !important; max-width: 720px !important; }

/* 텍스트 기본색 */
h1, h2, h3, p, span, label, div, li, caption {
    color: #191f28 !important;
}

/* 버튼 */
.stButton > button {
    background: #3182f6 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.75rem 0 !important;
    width: 100% !important;
    margin-top: 0.5rem !important;
}
.stButton > button:hover { background: #1c6ef2 !important; }

/* 탭 */
.stTabs [data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: #8b95a1 !important;
}
.stTabs [aria-selected="true"] {
    color: #191f28 !important;
    border-bottom: 2px solid #3182f6 !important;
}

/* 입력 */
input, textarea {
    background: #fff !important;
    color: #191f28 !important;
    border-radius: 8px !important;
}

/* expander */
details {
    background: #fff !important;
    border: 1px solid #e0e4ea !important;
    border-radius: 12px !important;
}

/* 구분선 */
hr { border: none !important; border-top: 1px solid #e0e4ea !important; }

/* caption */
small, .stCaption { color: #8b95a1 !important; }

/* 사이드바 완전 숨김 */
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
USER_NAME = "수철"
TICKERS = {
    "금현물": "IAU", "나스닥100": "QQQ",
    "현금(소파)": "UUP", "한국리츠": "088980.KS",
}
IS_USD = {"금현물": True, "나스닥100": True, "현금(소파)": True, "한국리츠": False}
COLORS = ["#3182f6", "#ff6b35", "#00c471", "#8b95a1"]
LABEL_EN = {"일시납": "Lump-sum", "월적립": "DCA", "혼합": "Hybrid", "커스텀": "Custom"}

if "history" not in st.session_state:
    st.session_state.history = []

# ── 유틸 ──────────────────────────────────────────────────
def fmt(v):
    s = "-" if v < 0 else ""
    v = abs(v)
    uk = int(v // 1e8); mn = int((v % 1e8) // 1e4)
    if uk > 0 and mn > 0: return f"{s}₩{uk:,}억 {mn:,}만"
    if uk > 0: return f"{s}₩{uk:,}억"
    if mn > 0: return f"{s}₩{mn:,}만"
    return f"{s}₩{int(v):,}"

def fmts(v): return ("+" if v >= 0 else "") + fmt(v)

def card_html(title, rows, color="#3182f6"):
    rows_html = "".join([
        f'<div style="display:flex;justify-content:space-between;'
        f'padding:8px 0;border-bottom:1px solid #f0f2f5;">'
        f'<span style="color:#8b95a1;font-size:0.87rem;">{k}</span>'
        f'<span style="font-weight:700;color:{vc};font-size:0.9rem;">{v}</span></div>'
        for k, v, vc in rows
    ])
    return f"""
<div style="background:#fff;border-radius:14px;padding:18px 20px;
            border:1px solid #e0e4ea;margin-bottom:14px;">
  <div style="font-size:0.72rem;font-weight:800;letter-spacing:0.1em;
              text-transform:uppercase;color:{color};border-bottom:2px solid {color};
              padding-bottom:7px;margin-bottom:12px;">{title}</div>
  {rows_html}
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
    raw.dropna(how="all", inplace=True); raw.ffill(inplace=True)
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
    w = np.array([weights[n] for n in names])
    ya = np.array([yields[n] for n in names])
    dep = schedule(cfg, prices.index)
    rebal = set()
    for yr in prices.index.year.unique():
        for mo in [1, 7]:
            mask = (prices.index.year == yr) & (prices.index.month == mo)
            if mask.any(): rebal.add(prices.index[mask][0])
    sh, cash, inv, pv, iv, pm = np.zeros(len(names)), 0., 0., [], [], None
    for dt, rw in prices.iterrows():
        pa = rw[names].values.astype(float)
        sp = np.where(pa > 0, pa, 1.)
        if dt.month != pm:
            sh += (sh * pa) * ya / sp; pm = dt.month
        if len(dep) > 0 and dt in dep.index:
            cash += dep[dt]; inv += dep[dt]
            sh += (cash * w) / sp; cash = 0.
        if dt in rebal and sh.sum() > 0:
            cv = (sh * pa).sum()
            tc = np.abs(cv * w - sh * pa).sum() * cost
            sh = ((cv - tc) * w) / sp
        pv.append((sh * pa).sum() + cash); iv.append(inv)
    return pd.Series(pv, index=prices.index), pd.Series(iv, index=prices.index)

# ── 지표 ──────────────────────────────────────────────────
def metrics(pf, inv):
    ti = inv.iloc[-1]; fv = pf.iloc[-1]
    ret = (fv - ti) / ti if ti > 0 else 0
    diff = inv.diff().fillna(0); diff.iloc[0] = inv.iloc[0]
    cf = (diff[diff > 0] * -1.).copy()
    cf[pf.index[-1]] = cf.get(pf.index[-1], 0) + fv
    full = pd.Series(0., index=pf.index)
    for d, v in cf.sort_index().items(): full[d] += v
    try:
        vals = np.where(np.isfinite(full.values), full.values, 0.)
        irr = npf.irr(vals)
        cagr = (1 + irr) ** 252 - 1 if np.isfinite(irr) and irr > -1 else 0.
    except: cagr = 0.
    dep_days = set(diff[diff > 0].index)
    prev = pf.shift(1).bfill(); dc = pf.diff().fillna(0)
    twr = pd.Series(0., index=pf.index)
    for d in pf.index:
        if d not in dep_days and prev[d] > 0: twr[d] = dc[d] / prev[d]
    vol = twr.std() * np.sqrt(252)
    if not np.isfinite(vol): vol = 0.
    return dict(ti=ti, fv=fv, profit=fv-ti, ret=ret*100,
                cagr=cagr*100, vol=vol*100,
                sharpe=(cagr-0.035)/vol if vol > 0 else 0,
                mdd=((pf-pf.cummax())/pf.cummax()).min()*100,
                years=(pf.index[-1]-pf.index[0]).days/365.25)

# ── 차트 ──────────────────────────────────────────────────
def chart(results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5.5),
                                    facecolor="#fff", dpi=110)
    fig.subplots_adjust(hspace=0.55)
    for ax in (ax1, ax2):
        ax.set_facecolor("#fff")
        ax.tick_params(colors="#8b95a1", labelsize=7.5)
        for sp in ax.spines.values(): sp.set_edgecolor("#e8eaed"); sp.set_linewidth(0.6)
        ax.grid(alpha=0.5, color="#f2f4f6", linewidth=0.5)
    for i, (name, (pf, inv)) in enumerate(results.items()):
        c = COLORS[i % len(COLORS)]; lb = LABEL_EN.get(name, name)
        ax1.plot(pf.index, pf/1e8, color=c, lw=1.6, label=lb)
        ax1.plot(inv.index, inv/1e8, color=c, lw=0.8, ls="--", alpha=0.45)
    ax1.set_title("Value vs Invested  (solid / dashed)", fontsize=8.5,
                  color="#8b95a1", pad=7, loc="left")
    ax1.set_ylabel("Billion KRW", fontsize=7.5, color="#8b95a1")
    ax1.legend(facecolor="#fff", edgecolor="#e8eaed", fontsize=7.5,
               ncol=len(results), loc="upper left")
    for i, (name, (pf, inv)) in enumerate(results.items()):
        c = COLORS[i % len(COLORS)]; lb = LABEL_EN.get(name, name)
        dd = (pf - pf.cummax()) / pf.cummax() * 100
        ax2.fill_between(dd.index, dd, 0, alpha=0.1, color=c)
        ax2.plot(dd.index, dd, color=c, lw=1.1, label=lb)
    ax2.set_title("Drawdown (%)", fontsize=8.5, color="#8b95a1", pad=7, loc="left")
    ax2.set_ylabel("%", fontsize=7.5, color="#8b95a1")
    ax2.legend(facecolor="#fff", edgecolor="#e8eaed", fontsize=7.5, ncol=len(results))
    fig.patch.set_facecolor("#fff")
    plt.tight_layout(pad=1.8)
    return fig

# ════════════════════════════════════════════════════════════
#  메인 UI
# ════════════════════════════════════════════════════════════
st.markdown(f"# 포트폴리오 백테스터")
st.markdown(
    f'안녕하세요, **{USER_NAME}님**. '
    f'아래에서 시나리오를 설정하고 백테스트를 실행하세요.'
)

# ── 설정 (expander) ───────────────────────────────────────
with st.expander("⚙️ 포트폴리오 설정", expanded=False):
    st.markdown("**백테스트 기간**")
    c1, c2 = st.columns(2)
    start_date = c1.date_input("시작", value=date(2016,1,1),
                                min_value=date(2010,1,1), max_value=date(2024,1,1),
                                label_visibility="collapsed")
    end_date   = c2.date_input("종료", value=date(2025,6,30),
                                min_value=date(2011,1,1), max_value=date(2025,12,31),
                                label_visibility="collapsed")
    st.caption(f"{start_date} ~ {end_date}")

    st.markdown("**자산 비중 (%)**")
    w_g = st.slider("금현물",     0, 100, 25, 5)
    w_n = st.slider("나스닥100",  0, 100, 25, 5)
    w_c = st.slider("현금(소파)", 0, 100, 25, 5)
    w_r = st.slider("한국리츠",   0, 100, 25, 5)
    tw  = w_g + w_n + w_c + w_r
    if tw == 0: st.error("비중 합계가 0입니다."); st.stop()
    if tw != 100: st.warning(f"합계 {tw}% → 자동 정규화")
    weights = {k: v/tw for k, v in
               {"금현물": w_g, "나스닥100": w_n,
                "현금(소파)": w_c, "한국리츠": w_r}.items()}

    st.markdown("**연간 배당/분배금률 (%)**")
    y_g = st.number_input("금현물",     0.0, 20.0, 0.0, 0.1)
    y_n = st.number_input("나스닥100",  0.0, 20.0, 3.0, 0.1)
    y_c = st.number_input("현금(소파)", 0.0, 20.0, 4.0, 0.1)
    y_r = st.number_input("한국리츠",   0.0, 20.0, 6.5, 0.1)
    yields = {
        "금현물": y_g/100/12, "나스닥100": y_n/100/12,
        "현금(소파)": y_c/100/12, "한국리츠": y_r/100/12,
    }

    st.markdown("**리밸런싱 수수료 (%)**")
    cost = st.slider("수수료", 0.0, 2.0, 0.5, 0.05) / 100

    run_label = st.text_input("이번 테스트 이름 (선택)",
                               placeholder="예: 공격형 포트폴리오")

# ── 시나리오 탭 ───────────────────────────────────────────
st.markdown("---")
st.markdown("### 입금 시나리오")
tab_a, tab_b, tab_c, tab_d = st.tabs(["A. 일시납", "B. 월적립", "C. 혼합", "D. 커스텀"])
scenarios = {}

with tab_a:
    st.caption("전체 자금을 첫날 한 번에 투입합니다.")
    en_a  = st.checkbox("활성화", value=True, key="en_a")
    ini_a = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             100_000_000, 1_000_000, key="ini_a", format="%d")
    st.caption(f"= {fmt(ini_a)}")
    scenarios["일시납"] = {"enabled": en_a, "initial": ini_a, "dca": 0, "freq": None, "custom": {}}

with tab_b:
    st.caption("매월 일정 금액을 꾸준히 적립합니다.")
    en_b  = st.checkbox("활성화", value=True, key="en_b")
    dca_b = st.number_input("월 적립금 (원)", 0, 100_000_000,
                             3_000_000, 500_000, key="dca_b", format="%d")
    st.caption(f"월 {fmt(dca_b)} × 12 = 연 {fmt(dca_b*12)}")
    scenarios["월적립"] = {"enabled": en_b, "initial": 0, "dca": dca_b, "freq": "MS", "custom": {}}

with tab_c:
    st.caption("초기 목돈 + 매월 추가 적립합니다.")
    en_c  = st.checkbox("활성화", value=True, key="en_c")
    ini_c = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             50_000_000, 1_000_000, key="ini_c", format="%d")
    dca_c = st.number_input("월 적립금 (원)", 0, 100_000_000,
                             2_000_000, 500_000, key="dca_c", format="%d")
    st.caption(f"초기 {fmt(ini_c)} + 월 {fmt(dca_c)}")
    scenarios["혼합"] = {"enabled": en_c, "initial": ini_c, "dca": dca_c, "freq": "MS", "custom": {}}

with tab_d:
    st.caption("특정 시점에 비정기 입금합니다.")
    en_d  = st.checkbox("활성화", value=True, key="en_d")
    ini_d = st.number_input("초기 투입금 (원)", 0, 10_000_000_000,
                             30_000_000, 1_000_000, key="ini_d", format="%d")
    st.caption("형식: 2023-03-01: 10000000")
    ct = st.text_area("입금 일정", (
        "2022-04-01: 10000000\n2022-10-01: 15000000\n"
        "2023-03-01: 10000000\n2023-09-01: 20000000\n2024-01-01: 5000000"
    ), height=120, key="ct")
    cds = {}
    for line in ct.strip().split("\n"):
        try:
            p = line.replace(",","").split(":")
            cds[p[0].strip()] = float(p[1].strip())
        except: pass
    tcd = sum(cds.values())
    st.caption(f"합계: {fmt(tcd)} ({len(cds)}건) | 총 투입 예상: {fmt(ini_d+tcd)}")
    scenarios["커스텀"] = {"enabled": en_d, "initial": ini_d, "dca": 0,
                           "freq": None, "custom": cds}

# ── 실행 버튼 ─────────────────────────────────────────────
st.markdown("---")
run_btn = st.button("백테스트 실행")

if run_btn:
    enabled = {k: v for k, v in scenarios.items() if v.get("enabled")}
    if not enabled:
        st.warning("하나 이상의 시나리오를 활성화하세요.")
        st.stop()

    # ── 1단계: 데이터 수집 ──
    prog = st.empty()
    prog.info("📡 1/3  시장 데이터 수집 중...")
    with st.spinner("Yahoo Finance에서 데이터를 받아오는 중입니다. 잠시만 기다려 주세요."):
        try:
            prices, fx = fetch(str(start_date), str(end_date))
            prog.info(f"✅ 1/3  데이터 수집 완료 — {len(prices)}거래일")
        except Exception as e:
            prog.error(f"❌ 데이터 수집 실패: {e}")
            st.stop()

    # ── 2단계: 계산 ──
    prog.info("⚙️ 2/3  백테스트 계산 중...")
    with st.spinner("시나리오별 수익률을 계산하고 있습니다..."):
        results = {}
        for name, cfg in enabled.items():
            pf, inv = backtest(prices, weights, yields, cfg, cost)
            results[name] = (pf, inv)
        prog.info(f"✅ 2/3  계산 완료 — {len(results)}개 시나리오")

    prog.success("✅ 3/3  백테스트 완료!")

    # 환율 정보
    fx_chg = (fx.iloc[-1] / fx.iloc[0] - 1) * 100
    st.info(
        f"원달러 환율: {str(start_date)[:7]} {fx.iloc[0]:.0f}원 → "
        f"{str(end_date)[:7]} {fx.iloc[-1]:.0f}원 ({fx_chg:+.1f}%)"
    )

    # ── 3단계: 성과 카드 (최우선) ──
    st.markdown("## 📊 시나리오별 성과")
    for i, (name, (pf, inv)) in enumerate(results.items()):
        m = metrics(pf, inv)
        c = COLORS[i % len(COLORS)]
        pc = "#3182f6" if m["profit"] >= 0 else "#f04452"
        cc = "#3182f6" if m["cagr"]   >= 0 else "#f04452"
        rows = [
            ("총 투입금",   fmt(m["ti"]),          "#191f28"),
            ("최종 자산",   fmt(m["fv"]),           "#191f28"),
            ("수익금",      fmts(m["profit"]),       pc),
            ("누적 수익률", f'{m["ret"]:+.2f}%',    pc),
            ("CAGR (IRR)",  f'{m["cagr"]:+.2f}%',   cc),
            ("연간 변동성", f'{m["vol"]:.2f}%',      "#191f28"),
            ("샤프 비율",   f'{m["sharpe"]:.2f}',    "#191f28"),
            ("최대 낙폭",   f'{m["mdd"]:.2f}%',      "#f04452"),
            ("기간",        f'{m["years"]:.1f}년',   "#191f28"),
        ]
        st.markdown(card_html(name, rows, c), unsafe_allow_html=True)

    # ── 4단계: 비교 테이블 ──
    st.markdown("## 📋 한눈에 비교")
    tbl = []
    for name, (pf, inv) in results.items():
        m = metrics(pf, inv)
        tbl.append({"시나리오": name, "총 투입금": fmt(m["ti"]),
                    "최종 자산": fmt(m["fv"]), "수익률": f'{m["ret"]:+.2f}%',
                    "CAGR": f'{m["cagr"]:+.2f}%', "MDD": f'{m["mdd"]:.2f}%'})
    st.dataframe(pd.DataFrame(tbl).set_index("시나리오"), use_container_width=True)

    # ── 5단계: 기록 저장 ──
    label = run_label.strip() if run_label.strip() else f"테스트 {len(st.session_state.history)+1}"
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "label": label, "period": f"{start_date} ~ {end_date}",
        "scenarios": {n: {"수익률": f'{metrics(pf,inv)["ret"]:+.2f}%',
                          "CAGR": f'{metrics(pf,inv)["cagr"]:+.2f}%'}
                      for n, (pf, inv) in results.items()},
    }
    st.session_state.history.insert(0, entry)
    st.success(f"'{label}' 결과가 기록 보관함에 저장되었습니다.")

    # ── 6단계: 차트 ──
    st.markdown("## 📈 성과 차트")
    try:
        fig = chart(results)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as e:
        st.warning(f"차트 표시 실패 (위 수치 결과는 정상): {e}")

    # ── 다운로드 ──
    json_out = {}
    for name, (pf, inv) in results.items():
        m = metrics(pf, inv)
        pf_m = pf.resample("ME").last()
        im_m = inv.resample("ME").last()
        json_out[name] = {
            "metrics": {k: round(v,2) for k,v in m.items()},
            "dates":   [d.strftime("%Y-%m") for d in pf_m.index],
            "portfolio":[round(v) for v in pf_m.values],
            "invested": [round(v) for v in im_m.values],
        }
    st.download_button("결과 JSON 다운로드",
        data=json.dumps(json_out, ensure_ascii=False, indent=2).encode(),
        file_name="backtest_results.json", mime="application/json")

# ════════════════════════════════════════════════════════════
#  기록 보관함
# ════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🗂 기록 보관함")
if not st.session_state.history:
    st.caption(f"{USER_NAME}님의 백테스트 기록이 아직 없습니다.")
else:
    st.caption(f"총 {len(st.session_state.history)}건 · 앱 재시작 시 초기화")
    for i, e in enumerate(st.session_state.history):
        with st.expander(f"{e['label']}  ·  {e['timestamp']}"):
            st.caption(e["period"])
            for sc, sm in e["scenarios"].items():
                st.markdown(f"**{sc}** — 수익률 {sm['수익률']} / CAGR {sm['CAGR']}")
            if st.button("삭제", key=f"d{i}"):
                st.session_state.history.pop(i); st.rerun()

st.markdown("---")
st.caption("데이터: Yahoo Finance · IAU·QQQ·UUP KRW=X 환율 적용 · 088980.KS 원화 직접 · 투자 참고용")
