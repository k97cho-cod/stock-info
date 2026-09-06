import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 화면 넓게 설정 및 패딩 타이트하게 조정
st.set_page_config(page_title="종목 맞춤형 대시보드", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 0.2rem; padding-bottom: 0.5rem; padding-left: 1rem; padding-right: 1rem; }
        h3 { font-size: 1rem !important; margin-top: 0.5rem !important; margin-bottom: 0.2rem !important; }
        p, div, span { font-size: 0.8rem !important; }
        .tech-table { width: auto; border-collapse: collapse; margin-top: 0.2rem; }
        .tech-table th, .tech-table td { padding: 4px 16px 4px 0px; text-align: left; font-size: 0.8rem; }
        .tech-table th { color: #555; font-weight: normal; }
        .tech-table td { font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 1. 맨 위: 종목코드 입력창 한 줄 배치
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
# [상단 영역] 전체 폭 활용 (1번, 2번, 4번 순서대로 가로 정렬)
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

# 2번과 4번을 좌우로 나란히 배치하여 공간 활용도 극대화
top_sub1, top_sub2 = st.columns([5, 5], gap="medium")

with top_sub1:
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

with top_sub2:
    # 4. 최근 주요 뉴스 (제목 포함 3줄)
    st.markdown("### 4. 최근 주요 뉴스")
    news_items = stock.news
    if news_items:
        for item in news_items[:3]:
            st.markdown(f"- [{item.get('title', '제목없음')}]({item.get('link', '#')})")
    else:
        st.write("관련 뉴스가 없습니다.")

st.markdown("---")

# ==========================================
# [하단 영역] 3. 재무 및 밸류에이션 차트 (전체 폭에서 좌우 4개씩 분할)
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
                textfont=dict(size=10, color='black', family="Arial Black"),
                line=dict(color=color_code, width=2),
                marker=dict(size=5)
            ))
    else:
        if idx is not None and values is not None:
            fig.add_trace(go.Scatter(
                x=idx, 
                y=values,
                mode='lines+markers+text',
                text=values.round(1).astype(str) + unit_str,
                textposition='top center',
                textfont=dict(size=10, color='black', family="Arial Black"),
                line=dict(color=color_code, width=2),
                marker=dict(size=5)
            ))

    fig.update_layout(
        title=dict(text=title_text, font=dict(size=10, color='black')),
        margin=dict(l=2, r=2, t=18, b=2),
        height=85,
        xaxis=dict(showgrid=True, tickfont=dict(size=8, color='black')),
        yaxis=dict(showgrid=True, tickfont=dict(size=7, color='gray')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# 하단을 좌우 2열로 나누어 각각 4개씩 배치
chart_col1, chart_col2 = st.columns(2, gap="medium")

with chart_col1:
    draw_chart_box(fin_T, 'Total Revenue', '🔹 매출액 (억원)', '#8e44ad', 1e8, '억')
    draw_chart_box(fin_T, 'Operating Income', '🔹 영업이익 (억원)', '#9b59b6', 1e8, '억')
    draw_chart_box(fin_T, 'Net Income', '🔹 당기순이익 (억원)', '#2980b9', 1e8, '억')
    draw_chart_box(bs_T, 'Total Liabilities Net Minority Interest', '🔹 부채총계 (억원)', '#e67e22', 1e8, '억')

with chart_col2:
    roe_val = info.get('returnOnEquity', 0.0902) * 100
    eps_val = info.get('trailingEps', 0)
    per_val = info.get('trailingPE', 0)
    pbr_val = info.get('priceToBook', 0)

    if not fin_T.empty:
        idx = fin_T.index.strftime('%Y-%m')
        draw_chart_box(None, None, '🔹 ROE 추이 (%)', '#27ae60', 1.0, '%', True, idx, pd.Series([roe_val] * len(idx), index=idx))
        draw_chart_box(None, None, '🔹 EPS 추이 (원)', '#d35400', 1.0, '원', True, idx, pd.Series([eps_val] * len(idx), index=idx))
        draw_chart_box(None, None, '🔹 PER 추이 (배)', '#c0392b', 1.0, '배', True, idx, pd.Series([per_val] * len(idx), index=idx))
        draw_chart_box(None, None, '🔹 PBR 추이 (배)', '#16a085', 1.0, '배', True, idx, pd.Series([pbr_val] * len(idx), index=idx))
