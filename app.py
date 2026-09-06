import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 페이지 기본 설정
st.set_page_config(page_title="나만의 종목 분석 대시보드", layout="wide")

st.title("📈 나만의 맞춤형 종목 대시보드")

# 종목코드 입력창 (기본값: KCTC 009070.KS)
ticker_input = st.text_input("종목코드를 입력하세요 (예: 009070.KS, 005930.KS)", value="009070.KS")

# WMA(가중이동평균) 계산 함수
def calc_wma(series, window):
    weights = np.arange(1, window + 1)
    return series.rolling(window).apply(lambda weights_slice: np.dot(weights_slice, weights) / weights.sum(), raw=True)

if ticker_input:
    stock = yf.Ticker(ticker_input)
    
    # 1. 기업 개요 및 주요 수익원 (2줄 요약)
    st.subheader("1. 기업 개요 및 주요 수익원")
    info = stock.info
    summary = info.get('longBusinessSummary', '기업 개요 데이터가 제공되지 않는 종목입니다.')
    # 약 2줄 분량으로 잘라서 출력
    st.write(summary[:200] + "..." if len(summary) > 200 else summary)

    # 2. 기술적 조건 검증
    st.subheader("2. 기술적 조건 검증")
    hist = stock.history(period="1y")
    
    if len(hist) >= 200:
        # WMA 60일, 200일 계산
        close_series = hist['Close']
        hist['WMA60'] = calc_wma(close_series, 60)
        hist['WMA200'] = calc_wma(close_series, 200)
        
        last_wma60 = hist['WMA60'].iloc[-1]
        last_wma200 = hist['WMA200'].iloc[-1]
        
        # 두 이평선 간 이격률 계산 (|WMA60 - WMA200| / WMA200 * 100)
        disparity = abs(last_wma60 - last_wma200) / last_wma200 * 100
        cond_wma = "YES" if disparity <= 10 else "NO"
        
        col1, col2, col3 = st.columns(3)
        col1.metric("WMA 60-200일 이격 10% 이내", f"{cond_wma} ({disparity:.2f}%)")
        col2.metric("WMA 60일", f"{last_wma60:,.0f}원")
        col3.metric("WMA 200일", f"{last_wma200:,.0f}원")
    else:
        st.info("이동평균선 계산을 위한 데이터가 충분하지 않습니다.")

    # 3. 재무 꺾은선 점차트
    st.subheader("3. 재무 및 밸류에이션 추이 (점차트)")
    
    # 분기 재무제표 데이터 불러오기
    financials = stock.quarterly_financials
    balance = stock.quarterly_balance_sheet
    
    if not financials.empty:
        # 데이터 정렬 (과거 -> 최근)
        fin_df = financials.iloc[:, ::-1]
        
        # 지정된 8개 지표 수집
        dates = fin_df.columns.strftime('%Y-%m')
        
        rev = fin_df.loc['Total Revenue'].values if 'Total Revenue' in fin_df.index else None
        op_inc = fin_df.loc['Operating Income'].values if 'Operating Income' in fin_df.index else None
        net_inc = fin_df.loc['Net Income'].values if 'Net Income' in fin_df.index else None
        
        # 차트 시각화
        metrics = [
            ("① 매출액", rev),
            ("② 영업이익", op_inc),
            ("③ 당기순이익", net_inc)
        ]
        
        for title, val in metrics:
            if val is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=val, mode='lines+markers', name=title, line=dict(width=2), marker=dict(size=8)))
                fig.update_layout(title=title, height=250, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)

        # 주요 투자지표 요약 (PER, EPS, ROE, 부채비율, PBR)
        st.markdown("**④ PER / ⑤ EPS / ⑥ ROE / ⑦ 부채비율 / ⑧ PBR (현재 기준 요약)**")
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        
        m_col1.metric("PER", f"{info.get('trailingPE', 'N/A')} 배")
        m_col2.metric("EPS", f"{info.get('trailingEps', 'N/A')} 원")
        m_col3.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.2f} %" if info.get('returnOnEquity') else "N/A")
        m_col4.metric("부채비율", f"{info.get('debtToEquity', 'N/A')} %")
        m_col5.metric("PBR", f"{info.get('priceToBook', 'N/A')} 배")

    # 4. 최근 주요 뉴스
    st.subheader("4. 최근 주요 뉴스")
    news_list = stock.news
    if news_list:
        for item in news_list[:3]:
            title = item.get('title', '제목 없음')
            link = item.get('link', '#')
            st.markdown(f"- [{title}]({link})")
    else:
        st.write("관련 최신 뉴스가 없습니다.")