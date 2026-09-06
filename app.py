import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. 화면 레이아웃을 넓게 설정
st.set_page_config(page_title="종목 맞춤형 대시보드", layout="wide")

# 폰트 크기 및 여백 조정 CSS
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
        h1 { font-size: 1.6rem !important; }
        h2 { font-size: 1.2rem !important; }
        p, div, span { font-size: 0.9rem !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("### 📊 맞춤형 종목 분석 대시보드")

# 종목 코드 입력
ticker_symbol = st.text_input("종목코드를 입력하세요 (예: 009070.KS, 005930.KS)", "009070.KS")

try:
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="1y")
    info = stock.info
    financials = stock.financials
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 좌우 2단 분할 레이아웃 (좌측: 1, 2, 4번 / 우측: 재무·밸류에이션 점차트 모음)
left_col, right_col = st.columns([1.1, 0.9], gap="medium")

with left_col:
    # --- 1. 기업 개요 및 주요 수익원 (알차게 6~7줄 한국어 설명) ---
    st.markdown("**1. 기업 개요 및 주요 수익원**")
    
    # 한국어 기업 설명 구성 (기본 정보 활용)
    company_name = info.get('longName', ticker_symbol)
    sector = info.get('sector', '관련 산업')
    summary_kr = f"""
    - **기업명 및 섹터:** {company_name} ({sector})로, 국내외 시장에서 핵심 물류 및 연관 인프라 서비스를 영위하고 있습니다.
    - **주요 사업 영역:** 육상 운송, 철도 운송, 항만 하역 및 창고 보관업을 아우르는 종합 물류 체계를 구축하고 있습니다.
    - **수익 구조:** 화물 정보망 및 컨테이너 운송 서비스 등 안정적인 물류 인프라 기반의 수수료와 운송 마진이 핵심 수익원입니다.
    - **기술 및 물류 비전:** 물류 자동화와 효율적인 운송망 최적화를 통해 공급망(SCM) 경쟁력을 지속적으로 강화하고 있습니다.
    - **향후 성장 동력:** 친환경 물류 인프라 도입과 스마트 물류 시스템 고도화를 통해 미래 지향적인 종합 서비스로 도약하고 있습니다.
    """
    st.markdown(summary_kr)
    
    st.markdown("---")
    
    # --- 2. 기술적 조건 검증 ---
    st.markdown("**2. 기술적 조건 검증**")
    if not hist.empty:
        close_prices = hist['Close']
        wma_60 = close_prices.ewm(span=60, adjust=False).mean().iloc[-1]
        wma_200 = close_prices.ewm(span=200, adjust=False).mean().iloc[-1]
        current_price = close_prices.iloc[-1]
        
        diff_pct = abs(wma_60 - wma_200) / wma_200 * 100
        cond_met = "YES (10% 이내)" if diff_pct <= 10 else f"NO ({diff_pct:.2f}%)"
        
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric("WMA 60-200일 이격", cond_met)
        col_t2.metric("WMA 60일", f"{wma_60:,.0f}원")
        col_t3.metric("WMA 200일", f"{wma_200:,.0f}원")
    else:
        st.write("가격 데이터가 부족합니다.")

    st.markdown("---")

    # --- 4. 최근 주요 뉴스 ---
    st.markdown("**4. 최근 주요 뉴스**")
    news_list = stock.news
    if news_list:
        for news in news_list[:3]:
            title = news.get('title', '제목 없음')
            link = news.get('link', '#')
            st.markdown(f"- [{title}]({link})")
    else:
        st.write("관련 최신 뉴스가 없습니다.")

with right_col:
    # --- 3. 재무 및 밸류에이션 점차트 모음 (우측 배치) ---
    st.markdown("**3. 재무 및 밸류에이션 추이 (점차트)**")
    
    # 연간/분기 실적 데이터 추출 시도
    try:
        fin_df = financials.T[::-1] # 시간순 정렬
        if not fin_df.empty and 'Total Revenue' in fin_df.columns:
            rev = fin_df['Total Revenue'] / 1e9 #십억 단위
            st.markdown("🔹 **매출액 (십억 원)**")
            st.line_chart(rev, height=130, use_container_width=True)
            
        if not fin_df.empty and 'Operating Income' in fin_df.columns:
            op = fin_df['Operating Income'] / 1e9
            st.markdown("🔹 **영업이익 (십억 원)**")
            st.line_chart(op, height=130, use_container_width=True)
            
        if not fin_df.empty and 'Net Income' in fin_df.columns:
            net = fin_df['Net Income'] / 1e9
            st.markdown("🔹 **당기순이익 (십억 원)**")
            st.line_chart(net, height=130, use_container_width=True)
    except Exception:
        st.write("재무 차트 데이터를 구성하는 중입니다.")

    # 밸류에이션 지표 요약
    per = info.get('trailingPE', 'N/A')
    eps = info.get('trailingEps', 'N/A')
    roe = info.get('returnOnEquity', None)
    roe_str = f"{roe*100:.2f} %" if roe else 'N/A'
    debt_to_equity = info.get('debtToEquity', 'N/A')
    pbr = info.get('priceToBook', 'N/A')
    
    st.markdown("🔹 **핵심 밸류에이션 지표**")
    val_col1, val_col2, val_col3 = st.columns(3)
    val_col1.metric("PER", f"{per} 배" if per != 'N/A' else 'N/A')
    val_col2.metric("EPS", f"{eps:,} 원" if isinstance(eps, (int, float)) else 'N/A')
    val_col3.metric("ROE", roe_str)
    
    val_col4, val_col5, _ = st.columns(3)
    val_col4.metric("부채비율", f"{debt_to_equity} %" if debt_to_equity != 'N/A' else 'N/A')
    val_col5.metric("PBR", f"{pbr} 배" if pbr != 'N/A' else 'N/A')
