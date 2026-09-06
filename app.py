import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 화면 넓게 설정 및 패딩 타이트하게 조정
st.set_page_config(page_title="종목 맞춤형 대시보드", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 0.8rem; padding-bottom: 0.5rem; padding-left: 1rem; padding-right: 1rem; }
        h3 { font-size: 1rem !important; margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
        p, div, span { font-size: 0.8rem !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("### 📊 맞춤형 종목 분석 대시보드")
ticker_symbol = st.text_input("종목코드 입력 (예: 009070.KS)", "009070.KS")

try:
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="1y")
    info = stock.info
    financials = stock.financials
    quarterly_fin = stock.quarterly_financials
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

left_col, right_col = st.columns(2, gap="medium")

with left_col:
    # 1. 기업 개요 및 주요 수익원
    st.markdown("### 1. 기업 개요 및 주요 수익원")
    name = info.get('longName', ticker_symbol)
    sector = info.get('sector', '관련 산업')
    summary_text = f"""
    - **기업 개요:** {name} ({sector})는 국내외 핵심 물류 및 운송 인프라를 구축한 전문 기업입니다.
    - **주요 사업 영역:** 육상·철도 운송, 항만 하역, 창고 보관 및 복합 물류 서비스를 포괄합니다.
    - **수익 구조:** 안정적인 화물 운송망과 물류 대행 수수료를 기반으로 탄탄한 현금흐름을 창출합니다.
    - **기술 및 물류 비전:** 스마트 물류 시스템 도입과 공급망(SCM) 고도화로 운영 효율을 극대화합니다.
    - **성장 전략:** 친환경 인프라 확충 및 물류 자동화 기술 접목을 통해 미래 경쟁력을 강화합니다.
    """
    st.markdown(summary_text)
    
    # 2. 기술적 조건 검증
    st.markdown("### 2. 기술적 조건 검증")
    if not hist.empty:
        close = hist['Close']
        w60 = close.ewm(span=60, adjust=False).mean().iloc[-1]
        w200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        diff = abs(w60 - w200) / w200 * 100
        cond = "YES (10% 이내)" if diff <= 10 else f"NO ({diff:.2f}%)"
        
        c1, c2, c3 = st.columns(3)
        c1.metric("WMA 60-200", cond)
        c2.metric("WMA 60일", f"{w60:,.0f}원")
        c3.metric("WMA 200일", f"{w200:,.0f}원")

    # 4. 최근 주요 뉴스
    st.markdown("### 4. 최근 주요 뉴스")
    news_items = stock.news
    if news_items:
        for item in news_items[:3]:
            st.markdown(f"- [{item.get('title', '제목없음')}]({item.get('link', '#')})")
    else:
        st.write("관련 뉴스가 없습니다.")

with right_col:
    # 3. 재무 및 밸류에이션 점차트 (Plotly 적용: 수치 표시 및 깔끔한 마커 라인)
    st.markdown("### 3. 재무 및 밸류에이션 추이")
    
    fin_source = quarterly_fin if not quarterly_fin.empty else financials
    if not fin_source.empty:
        fin_T = fin_source.T[::-1]
        
        def draw_plotly_chart(df, col_name, title_text, color_code):
            if col_name in df.columns:
                sub_df = df[[col_name]].dropna()
                sub_df[col_name] = sub_df[col_name] / 1e8 # 억원 단위
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=sub_df.index.strftime('%Y-%m'), 
                    y=sub_df[col_name],
                    mode='lines+markers+text',
                    text=sub_df[col_name].round(0).astype(str) + '억',
                    textposition='top center',
                    textfont=dict(size=9),
                    line=dict(color=color_code, width=2),
                    marker=dict(size=6)
                ))
                fig.update_layout(
                    title=dict(text=title_text, font=dict(size=12)),
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=140,
                    xaxis=dict(showgrid=True, tickfont=dict(size=8)),
                    yaxis=dict(showgrid=True, tickfont=dict(size=8)),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        draw_plotly_chart(fin_T, 'Total Revenue', '🔹 매출액 추이 (억원)', '#9b59b6')
        draw_plotly_chart(fin_T, 'Operating Income', '🔹 영업이익 추이 (억원)', '#8e44ad')
        draw_plotly_chart(fin_T, 'Net Income', '🔹 당기순이익 추이 (억원)', '#2980b9')

    # 핵심 밸류에이션 지표
    per = info.get('trailingPE', info.get('forwardPE', 'N/A'))
    eps = info.get('trailingEps', 'N/A')
    roe = info.get('returnOnEquity', None)
    roe_str = f"{roe*100:.2f} %" if roe else 'N/A'
    debt = info.get('debtToEquity', 'N/A')
    pbr = info.get('priceToBook', 'N/A')
    
    st.markdown("🔹 **핵심 밸류에이션 지표**")
    v1, v2, v3 = st.columns(3)
    v1.metric("PER", f"{per} 배" if per != 'N/A' else 'N/A')
    v2.metric("EPS", f"{eps:,} 원" if isinstance(eps, (int, float)) else 'N/A')
    v3.metric("ROE", roe_str)
    
    v4, v5, _ = st.columns(3)
    v4.metric("부채비율", f"{debt} %" if debt != 'N/A' else 'N/A')
    v5.metric("PBR", f"{pbr} 배" if pbr != 'N/A' else 'N/A')
