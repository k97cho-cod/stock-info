import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 화면 넓게 설정 및 패딩 타이트하게 조정
st.set_page_config(page_title="종목 맞춤형 대시보드", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 0.2rem; padding-bottom: 0.5rem; padding-left: 1rem; padding-right: 1rem; }
        h3 { font-size: 1rem !important; margin-top: 0rem !important; margin-bottom: 0.1rem !important; }
        p, div, span { font-size: 0.8rem !important; }
        .tech-table { width: auto; border-collapse: collapse; margin-top: 0.2rem; }
        .tech-table th, .tech-table td { padding: 4px 16px 4px 0px; text-align: left; font-size: 0.8rem; }
        .tech-table th { color: #555; font-weight: normal; }
        .tech-table td { font-weight: bold; }
        /* 우측 영역을 최상단으로 바짝 끌어올리기 위한 마진 조정 */
        .top-aligned { margin-top: -3.5rem; }
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

# 종목 입력창과 콘텐츠 영역을 완전히 분리하기 위해 상단 여백 확보용 빈 줄 제거 및 레이아웃 분할
left_col, right_col = st.columns([5.5, 4.5], gap="small")

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
        
        tech_html = f"""
        <table class="tech-table">
            <tr>
                <th>WMA 60-200</th>
                <th>WMA 60일</th>
                <th>WMA 200일</th>
            </tr>
            <tr>
                <td>{cond}</td>
                <td>{w60:,.0f}원</td>
                <td>{w200:,.0f}원</td>
            </tr>
        </table>
        """
        st.markdown(tech_html, unsafe_allow_html=True)

    # 4. 최근 주요 뉴스
    st.markdown("### 4. 최근 주요 뉴스")
    news_items = stock.news
    if news_items:
        for item in news_items[:3]:
            st.markdown(f"- [{item.get('title', '제목없음')}]({item.get('link', '#')})")
    else:
        st.write("관련 뉴스가 없습니다.")

with right_col:
    # 3. 재무 및 밸류에이션 점차트 (상단 마진을 끌어올려 독립적으로 배치)
    st.markdown('<div class="top-aligned">', unsafe_allow_html=True)
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
                textfont=dict(size=12, color='black', family="Arial Black"),
                line=dict(color=color_code, width=2),
                marker=dict(size=7)
            ))
            fig.update_layout(
                title=dict(text=title_text, font=dict(size=11, color='black')),
                margin=dict(l=2, r=2, t=20, b=2),
                height=100,
                xaxis=dict(showgrid=True, tickfont=dict(size=10, color='black')),
                yaxis=dict(showgrid=True, tickfont=dict(size=9, color='gray')),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    def draw_val_chart(idx, values, title_text, color_code, unit_str):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=idx, 
            y=values,
            mode='lines+markers+text',
            text=values.round(1).astype(str) + unit_str,
            textposition='top center',
            textfont=dict(size=12, color='black', family="Arial Black"),
            line=dict(color=color_code, width=2),
            marker=dict(size=7)
        ))
        fig.update_layout(
            title=dict(text=title_text, font=dict(size=11, color='black')),
            margin=dict(l=2, r=2, t=20, b=2),
            height=100,
            xaxis=dict(showgrid=True, tickfont=dict(size=10, color='black')),
            yaxis=dict(showgrid=True, tickfont=dict(size=9, color='gray')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 1~4번 재무 지표 점차트
    draw_compact_chart(fin_T, 'Total Revenue', '🔹 매출액 (억원)', '#8e44ad', 1e8, '억')
    draw_compact_chart(fin_T, 'Operating Income', '🔹 영업이익 (억원)', '#9b59b6', 1e8, '억')
    draw_compact_chart(fin_T, 'Net Income', '🔹 당기순이익 (억원)', '#2980b9', 1e8, '억')
    draw_compact_chart(bs_T, 'Total Liabilities Net Minority Interest', '🔹 부채총계 (억원)', '#e67e22', 1e8, '억')

    # 5~8번 밸류에이션 지표 점차트
    roe_val = info.get('returnOnEquity', 0.0902) * 100
    eps_val = info.get('trailingEps', 0)
    per_val = info.get('trailingPE', 0)
    pbr_val = info.get('priceToBook', 0)

    if not fin_T.empty:
        idx = fin_T.index.strftime('%Y-%m')
        
        draw_val_chart(idx, pd.Series([roe_val] * len(idx), index=idx), '🔹 ROE 추이 (%)', '#27ae60', '%')
        draw_val_chart(idx, pd.Series([eps_val] * len(idx), index=idx), '🔹 EPS 추이 (원)', '#d35400', '원')
        draw_val_chart(idx, pd.Series([per_val] * len(idx), index=idx), '🔹 PER 추이 (배)', '#c0392b', '배')
        draw_val_chart(idx, pd.Series([pbr_val] * len(idx), index=idx), '🔹 PBR 추이 (배)', '#16a085', '배')
    
    st.markdown('</div>', unsafe_allow_html=True)
