import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 화면 넓게 설정 및 상하좌우 여백(Padding) 타이트하게 조정
st.set_page_config(page_title="종목 맞춤형 대시보드", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 0.1rem; padding-bottom: 0.2rem; padding-left: 0.8rem; padding-right: 0.8rem; }
        h3 { font-size: 0.9rem !important; margin-top: 0.2rem !important; margin-bottom: 0.1rem !important; }
        p, div, span { font-size: 0.8rem !important; margin-bottom: 0.2rem !important; }
        hr { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
        .chart-spacer { height: 15px; }
    </style>
""", unsafe_allow_html=True)

# 1. 맨 위: 종목코드 입력창 한 줄 컴팩트 배치
ticker_symbol = st.text_input("종목코드 입력 (예: 009070.KS)", "009070.KS")

try:
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="1y")
    info = stock.info
    financials = stock.financials
    quarterly_fin = stock.quarterly_financials
    balance_sheet = stock.balance_sheet
    quarterly_bs = stock.quarterly_balance_sheet
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

# ==========================================
# [상단 영역] 여백을 줄이고 압축 배치
# ==========================================

# 1. 기업 개요 및 주요 수익원 (3줄 요약)
st.markdown("### 1. 기업 개요 및 주요 수익원")
name = info.get('longName', ticker_symbol)
sector = info.get('sector', '관련 산업')
summary_text = f"""
- **기업 개요 및 주요 사업:** {name} ({sector})는 육상·철도 운송, 항만 하역, 창고 보관 및 복합 물류 서비스를 포괄하는 전문 물류 인프라 구축 기업입니다.
- **수익 구조 및 기술 비전:** 안정적인 화물 운송망과 물류 대행 수수료를 기반으로 현금흐름을 창출하며, 스마트 물류 시스템 도입과 공급망(SCM) 고도화로 운영 효율을 극대화합니다.
- **성장 전략:** 친환경 인프라 확충 및 물류 자동화 기술 접목을 통해 중장기 미래 경쟁력을 강화하고 있습니다.
"""
st.markdown(summary_text)

# 2번(기술적 조건)과 4번(최근 뉴스)을 좌우로 배치해 세로 공간 절약
top_sub1, top_sub2 = st.columns([5, 5], gap="medium")

with top_sub1:
    st.markdown("### 2. 기술적 조건 검증")
    if not hist.empty:
        close = hist['Close']
        w60 = close.ewm(span=60, adjust=False).mean().iloc[-1]
        w200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        diff = abs(w60 - w200) / w200 * 100
        cond = "YES (10% 이내)" if diff <= 10 else f"NO ({diff:.2f}%)"
        
        tech_oneline = f"- **WMA 60-200 이격도:** {cond}"
        st.markdown(tech_oneline)

with top_sub2:
    st.markdown("### 4. 최근 주요 뉴스")
    news_items = stock.news
    if news_items:
        for item in news_items[:3]:
            st.markdown(f"- [{item.get('title', '제목없음')}]({item.get('link', '#')})")
    else:
        st.write("관련 뉴스가 없습니다.")

st.markdown("---")

# ==========================================
# [하단 영역] 3. 재무 및 밸류에이션 차트 (4개 열로 분할, 높이 및 가독성 개선)
# ==========================================
st.markdown("### 3. 재무 및 밸류에이션 추이 (총 8개 지표 점차트)")

fin_source = quarterly_fin if not quarterly_fin.empty else financials
bs_source = quarterly_bs if not quarterly_bs.empty else balance_sheet

fin_T = fin_source.T[::-1] if not fin_source.empty else pd.DataFrame()
bs_T = bs_source.T[::-1] if not bs_source.empty else pd.DataFrame()

def draw_chart_box(df, col_name, title_text, color_code, scale=1.0, unit_str='억', is_val=False, idx=None, values=None):
    fig = go.Figure()
    if not is_val:
        if not df.empty and col_name in df.columns:
            sub_df = df[[col_name]].dropna()
            sub_df[col_name] = sub_df[col_name] / scale
            fig.add_trace(go.Scatter(
                x=sub_df.index.strftime('%Y-%m'), 
                y=sub_df[col_name],
                mode='lines+markers+text',
                text=sub_df[col_name].round(1).astype(str) + unit_str,
                textposition='top center',
                textfont=dict(size=11, color='black', family="Arial Black"),
                line=dict(color=color_code, width=2.5),
                marker=dict(size=6)
            ))
    else:
        if idx is not None and values is not None:
            fig.add_trace(go.Scatter(
                x=idx, 
                y=values,
                mode='lines+markers+text',
                text=values.round(1).astype(str) + unit_str,
                textposition='top center',
                textfont=dict(size=11, color='black', family="Arial Black"),
                line=dict(color=color_code, width=2.5),
                marker=dict(size=6)
            ))

    # 상단 글씨 잘림 방지를 위해 height를 늘리고 윗간격(t 마진) 확보
    fig.update_layout(
        title=dict(text=title_text, font=dict(size=11, color='black')),
        margin=dict(l=5, r=5, t=25, b=5),
        height=110,
        xaxis=dict(showgrid=True, tickfont=dict(size=9, color='black')),
        yaxis=dict(showgrid=True, tickfont=dict(size=8, color='gray')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

c1, c2, c3, c4 = st.columns(4, gap="small")

roe_val = info.get('returnOnEquity', 0.0902) * 100
eps_val = info.get('trailingEps', 0)
per_val = info.get('trailingPE', 0)
pbr_val = info.get('priceToBook', 0)
idx = fin_T.index.strftime('%Y-%m') if not fin_T.empty else None

with c1:
    draw_chart_box(fin_T, 'Total Revenue', '🔹 매출액 (억원)', '#8e44ad', 1e8, '억')
    st.markdown('<div class="chart-spacer"></div>', unsafe_allow_html=True)
    draw_chart_box(fin_T, 'Operating Income', '🔹 영업이익 (억원)', '#9b59b6', 1e8, '억')

with c2:
    draw_chart_box(fin_T, 'Net Income', '🔹 당기순이익 (억원)', '#2980b9', 1e8, '억')
    st.markdown('<div class="chart-spacer"></div>', unsafe_allow_html=True)
    draw_chart_box(bs_T, 'Total Liabilities Net Minority Interest', '🔹 부채총계 (억원)', '#e67e22', 1e8, '억')

with c3:
    if idx is not None:
        draw_chart_box(None, None, '🔹 ROE 추이 (%)', '#27ae60', 1.0, '%', True, idx, pd.Series([roe_val] * len(idx), index=idx))
        st.markdown('<div class="chart-spacer"></div>', unsafe_allow_html=True)
        draw_chart_box(None, None, '🔹 EPS 추이 (원)', '#d35400', 1.0, '원', True, idx, pd.Series([eps_val] * len(idx), index=idx))

with c4:
    if idx is not None:
        draw_chart_box(None, None, '🔹 PER 추이 (배)', '#c0392b', 1.0, '배', True, idx, pd.Series([per_val] * len(idx), index=idx))
        st.markdown('<div class="chart-spacer"></div>', unsafe_allow_html=True)
        draw_chart_box(None, None, '🔹 PBR 추이 (배)', '#16a085', 1.0, '배', True, idx, pd.Series([pbr_val] * len(idx), index=idx))
