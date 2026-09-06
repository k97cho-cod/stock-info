import streamlit as st
import yfinance as yf
import pandas as pd

# 화면 레이아웃을 넓게 설정
st.set_page_config(page_title="종목 맞춤형 대시보드", layout="wide")

# 폰트 및 여백을 바짝 줄여서 한 화면에 들어오도록 CSS 조정
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0.5rem; padding-left: 1rem; padding-right: 1rem; }
        h3 { font-size: 1.1rem !important; margin-bottom: 0.3rem !important; }
        p, div, span { font-size: 0.8rem !important; }
    </style>
""", unsafe_allow_html=True,)

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

# 좌우 2단 레이아웃 (비율 1:1로 균형 맞춤)
left_col, right_col = st.columns(2, gap="medium")

with left_col:
    # 1. 기업 개요 (알차게 6~7줄 한국어 정리)
    st.markdown("### 1. 기업 개요 및 주요 수익원")
    name = info.get('longName', ticker_symbol)
    sector = info.get('sector', '관련 산업')
    summary_text = f"""
    - **기업 및 섹터:** {name} ({sector})로 국내외 물류 인프라 및 핵심 유통 서비스를 영위합니다.
    - **주요 사업 영역:** 육상 및 철도 운송, 항만 하역, 보관 및 복합 물류 체계를 구축하고 있습니다.
    - **수익 구조:** 안정적인 화물 운송망과 물류 대행 수수료를 통해 지속적인 현금흐름을 창출합니다.
    - **기술 및 물류 비전:** 스마트 물류 시스템 도입과 공급망(SCM) 고도화를 통해 운영 효율을 극대화합니다.
    - **성장 전략:** 친환경 인프라 확충 및 물류 자동화 기술 접목으로 미래 경쟁력을 강화하고 있습니다.
    """
    st.markdown(summary_text)
    
    st.markdown("---")
    
    # 2. 기술적 조건 검증
    st.markdown("### 2. 기술적 조건 검증")
    if not hist.empty:
        close = hist['Close']
        w60 = close.ewm(span=60, adjust=False).mean().iloc[-1]
        w200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        diff = abs(w60 - w200) / w200 * 100
        cond = "YES (10% 이내)" if diff <= 10 else f"NO ({diff:.2f}%)"
        
        c1, c2, c3 = st.columns(3)
        c1.metric("WMA 60-200 이격", cond)
        c2.metric("WMA 60일", f"{w60:,.0f}원")
        c3.metric("WMA 200일", f"{w200:,.0f}원")
    
    st.markdown("---")

    # 4. 최근 주요 뉴스
    st.markdown("### 4. 최근 주요 뉴스")
    news_items = stock.news
    if news_items:
        for item in news_items[:3]:
            st.markdown(f"- [{item.get('title', '제목없음')}]({item.get('link', '#')})")
    else:
        st.write("관련 뉴스가 없습니다.")

with right_col:
    # 3. 재무 및 밸류에이션 점차트 (모든 지표 포함 및 높이 축소)
    st.markdown("### 3. 재무 및 밸류에이션 추이")
    
    fin_source = financials if not financials.empty else quarterly_fin
    if not fin_source.empty:
        fin_T = fin_source.T[::-1]
        
        # 매출액 찾기
        rev_col = next((c for c in ['Total Revenue', 'Revenue'] if c in fin_T.columns), None)
        if rev_col:
            st.markdown("🔹 **매출액 (십억 원)**")
            st.line_chart(fin_T[rev_col] / 1e9, height=90, use_container_width=True)
            
        # 영업이익 찾기
        op_col = next((c for c in ['Operating Income', 'Operating Revenue'] if c in fin_T.columns), None)
        if op_col:
            st.markdown("🔹 **영업이익 (십억 원)**")
            st.line_chart(fin_T[op_col] / 1e9, height=90, use_container_width=True)
            
        # 당기순이익 찾기
        net_col = next((c for c in ['Net Income', 'Net Income Common Stockholders'] if c in fin_T.columns), None)
        if net_col:
            st.markdown("🔹 **당기순이익 (십억 원)**")
            st.line_chart(fin_T[net_col] / 1e9, height=90, use_container_width=True)

    # 핵심 밸류에이션 요약
    per = info.get('trailingPE', info.get('forwardPE', 'N/A'))
    eps = info.get('trailingEps', 'N/A')
    roe = info.get('returnOnEquity', None)
    roe_str = f"{roe*100:.2f} %" if roe else 'N/A'
    debt = info.get('debtToEquity', 'N/A')
    pbr = info.get('priceToBook', 'N/A')
    
    st.markdown("🔹 **핵심 밸류에이션 요약**")
    v1, v2, v3 = st.columns(3)
    v1.metric("PER", f"{per} 배" if per != 'N/A' else 'N/A')
    v2.metric("EPS", f"{eps:,} 원" if isinstance(eps, (int, float)) else 'N/A')
    v3.metric("ROE", roe_str)
    
    v4, v5, _ = st.columns(3)
    v4.metric("부채비율", f"{debt} %" if debt != 'N/A' else 'N/A')
    v5.metric("PBR", f"{pbr} 배" if pbr != 'N/A' else 'N/A')
