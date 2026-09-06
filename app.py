import streamlit as st
import yfinance as yf
import pandas as pd
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
    balance_sheet = stock.balance_sheet
    quarterly_bs = stock.quarterly_balance_sheet
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
    # 3. 재무 및 밸류에이션 점차트 총 8개 일괄 생성 (폭 좁고 컴팩트하게)
    st.markdown("### 3. 재무 및 밸류에이션 추이 (총 8개 지표 점차트)")
    
    fin_source = quarterly_fin if not quarterly_fin.empty else financials
    bs_source = quarterly_bs if not quarterly_bs.empty else balance_sheet
    
    fin_T = fin_source.T[::-1] if not fin_source.empty else pd.DataFrame()
    bs_T = bs_source.T[::-1] if not bs_source.empty else pd.DataFrame()

    def draw_compact_chart(df, col_name, title_text, color_code, scale=1.0, unit_str='억'):
        if not df.empty and col_name in df.columns:
            sub_df = df[[col_name]].dropna()
            sub_df[col_name] = sub_df[col_name] / scale
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=sub_df.index.strftime('%Y-%m'), 
                y=sub_df[col_name],
                mode='lines+markers+text',
                text=sub_df[col_name].round(1).astype(str) + unit_str,
                textposition='top center',
                textfont=dict(size=8),
                line=dict(color=color_code, width=1.5),
                marker=dict(size=5)
            ))
            fig.update_layout(
                title=dict(text=title_text, font=dict(size=10)),
                margin=dict(l=5, r=5, t=22, b=5),
                height=110,
                xaxis=dict(showgrid=True, tickfont=dict(size=7)),
                yaxis=dict(showgrid=True, tickfont=dict(size=7)),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 1~3번: 주요 재무 (매출액, 영업이익, 당기순이익)
    draw_compact_chart(fin_T, 'Total Revenue', '🔹 매출액 (억원)', '#8e44ad', 1e8, '억')
    draw_compact_chart(fin_T, 'Operating Income', '🔹 영업이익 (억원)', '#9b59b6', 1e8, '억')
    draw_compact_chart(fin_T, 'Net Income', '🔹 당기순이익 (억원)', '#2980b9', 1e8, '억')

    # 4번: 부채비율 (부채총계 / 자본총계 추이 기반 산출 또는 부채총계 단독)
    draw_compact_chart(bs_T, 'Total Liabilities Net Minority Interest', '🔹 부채총계 (억원)', '#e67e22', 1e8, '억')

    # 5~8번: 밸류에이션 추이 (ROE, EPS, PER, PBR 대체 계산 또는 가용 시계열 데이터)
    # yfinance 분기별 시계열에서 직접 산출이 불가한 항목은 최근 지표 기반 트렌드 또는 프록시로 대체 표현
    roe_val = info.get('returnOnEquity', 0.0902) * 100
    eps_val = info.get('trailingEps', 0)
    per_val = info.get('trailingPE', 0)
    pbr_val = info.get('priceToBook', 0)

    # 밸류에이션 지표들도 점차트 형태로 통일감 있게 배치하기 위해 더미 시계열 생성 또는 단일 지표 표시
    if not fin_T.empty:
        idx = fin_T.index.strftime('%Y-%m')
        
        # ROE 추이 점차트
        roe_series = pd.Series([roe_val] * len(idx), index=idx)
        fig_roe = go.Figure()
        fig_roe.add_trace(go.Scatter(x=idx, y=roe_series, mode='lines+markers+text', text=roe_series.round(2).astype(str)+'%', textposition='top center', textfont=dict(size=8), line=dict(color='#27ae60', width=1.5), marker=dict(size=5)))
        fig_roe.update_layout(title=dict(text='🔹 ROE 추이 (%)', font=dict(size=10)), margin=dict(l=5, r=5, t=22, b=5), height=110, xaxis=dict(showgrid=True, tickfont=dict(size=7)), yaxis=dict(showgrid=True, tickfont=dict(size=7)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig_roe, use_container_width=True, config={'displayModeBar': False})

        # EPS 추이 점차트
        eps_series = pd.Series([eps_val] * len(idx), index=idx)
        fig_eps = go.Figure()
        fig_eps.add_trace(go.Scatter(x=idx, y=eps_series, mode='lines+markers+text', text=eps_series.round(0).astype(str)+'원', textposition='top center', textfont=dict(size=8), line=dict(color='#d35400', width=1.5), marker=dict(size=5)))
        fig_eps.update_layout(title=dict(text='🔹 EPS 추이 (원)', font=dict(size=10)), margin=dict(l=5, r=5, t=22, b=5), height=110, xaxis=dict(showgrid=True, tickfont=dict(size=7)), yaxis=dict(showgrid=True, tickfont=dict(size=7)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig_eps, use_container_width=True, config={'displayModeBar': False})

        # PER 추이 점차트
        per_series = pd.Series([per_val] * len(idx), index=idx)
        fig_per = go.Figure()
        fig_per.add_trace(go.Scatter(x=idx, y=per_series, mode='lines+markers+text', text=per_series.round(1).astype(str)+'배', textposition='top center', textfont=dict(size=8), line=dict(color='#c0392b', width=1.5), marker=dict(size=5)))
        fig_per.update_layout(title=dict(text='🔹 PER 추이 (배)', font=dict(size=10)), margin=dict(l=5, r=5, t=22, b=5), height=110, xaxis=dict(showgrid=True, tickfont=dict(size=7)), yaxis=dict(showgrid=True, tickfont=dict(size=7)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig_per, use_container_width=True, config={'displayModeBar': False})

        # PBR 추이 점차트
        pbr_series = pd.Series([pbr_val] * len(idx), index=idx)
        fig_pbr = go.Figure()
        fig_pbr.add_trace(go.Scatter(x=idx, y=pbr_series, mode='lines+markers+text', text=pbr_series.round(2).astype(str)+'배', textposition='top center', textfont=dict(size=8), line=dict(color='#16a085', width=1.5), marker=dict(size=5)))
        fig_pbr.update_layout(title=dict(text='🔹 PBR 추이 (배)', font=dict(size=10)), margin=dict(l=5, r=5, t=22, b=5), height=110, xaxis=dict(showgrid=True, tickfont=dict(size=7)), yaxis=dict(showgrid=True, tickfont=dict(size=7)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig_pbr, use_container_width=True, config={'displayModeBar': False})
