import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import json
import os

# 페이지 설정
st.set_page_config(
    page_title="기후위기와 IT직업 변화 대시보드",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 폰트 설정
def set_korean_font():
    try:
        font_path = "/fonts/Pretendard-Bold.ttf"
        if os.path.exists(font_path):
            plt.rcParams['font.family'] = 'Pretendard'
            return True
    except:
        pass
    
    try:
        import matplotlib.font_manager as fm
        font_list = [f.name for f in fm.fontManager.ttflist]
        korean_fonts = ['Malgun Gothic', 'AppleGothic', 'NanumGothic']
        for font in korean_fonts:
            if font in font_list:
                plt.rcParams['font.family'] = font
                break
    except:
        pass
    return False

set_korean_font()
plt.rcParams['axes.unicode_minus'] = False

# 사이드바 위젯 정의 (코드 상단으로 이동)
with st.sidebar:
    st.header("🎛️ 대시보드 설정")
    
    show_insights = st.checkbox("💡 주요 인사이트", value=True)
    show_climate_data = st.checkbox("🌡️ 기후 변화 데이터", value=True)
    show_job_analysis = st.checkbox("💼 IT 직업 변화 분석", value=True)
        
    st.divider()
        
    if show_climate_data:
        st.subheader("🌍 기후 데이터 설정")
        climate_year_range = st.slider("연도 범위", 2000, 2022, (2015, 2022))
        top_countries_n = st.selectbox("상위 배출국 수", [5, 10, 15, 20], index=1)
        show_global_trend = st.checkbox("글로벌 트렌드 표시", value=True)
        chart_style = st.selectbox("차트 스타일", ["기본", "다크", "밝은"])
            
    st.divider()
        
    if show_job_analysis:
        st.subheader("💼 IT 직업 분석 설정")
        show_declining_jobs = st.checkbox("사라질 직업 포함", value=True)
        job_category_filter = st.selectbox("직업 카테고리", ["전체", "그린IT", "전통 IT", "기후테크"])
        skills_view = st.selectbox("역량 보기 방식", ["중요도 vs 성장률", "막대 차트", "레이더 차트"])
        prediction_years = st.slider("예측 연도 범위", 2022, 2030, (2024, 2030))
            
    st.divider()
        
    st.subheader("🎨 시각화 옵션")
    color_theme = st.selectbox("컬러 테마", ["기본", "청록색", "따뜻한 색조", "차가운 색조", "흑백"])
    show_data_labels = st.checkbox("데이터 레이블 표시", value=True)
    chart_height = st.slider("차트 높이", 400, 800, 500, 50)
        
    st.divider()
        
    st.subheader("📚 데이터 출처")
    st.markdown("""
    **1순위**: [Our World in Data](https://github.com/owid/co2-data)
    **2순위**: [World Bank API](https://data.worldbank.org/)
    **3순위**: 고품질 예시 데이터
    """)
        
    if st.button("🔄 데이터 다시 시도"):
        st.cache_data.clear()
        st.rerun()

# 컬러 테마 및 차트 템플릿 함수
def get_color_palette(theme):
    palettes = {
        "기본": px.colors.qualitative.Set1,
        "청록색": px.colors.sequential.Teal,
        "따뜻한 색조": px.colors.sequential.OrRd,
        "차가운 색조": px.colors.sequential.Blues,
        "흑백": px.colors.sequential.gray
    }
    return palettes.get(theme, px.colors.qualitative.Set1)

def get_chart_template(style):
    templates = {
        "기본": "plotly",
        "다크": "plotly_dark", 
        "밝은": "plotly_white"
    }
    return templates.get(style, "plotly")

# 시각화 옵션 변수 설정
color_palette = get_color_palette(color_theme)
chart_template = "plotly" 
if show_climate_data and 'chart_style' in locals():
    chart_template = get_chart_template(chart_style)

# 데이터 로딩 함수들
@st.cache_data(ttl=3600)
def load_climate_data():
    try:
        st.info("🔄 Our World in Data에서 실시간 데이터를 로드 중...")
        owid_url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
        df = pd.read_csv(owid_url)
        if 'country' in df.columns and 'year' in df.columns and 'co2' in df.columns:
            country_df = df[~df['country'].isin([
                'World', 'Asia', 'Europe', 'Africa', 'North America', 'South America',
                'Oceania', 'High-income countries', 'Low-income countries',
                'Middle-income countries', 'Upper-middle-income countries'
            ])].copy()
            climate_df = country_df[['country', 'year', 'co2']].copy()
            climate_df = climate_df.rename(columns={'co2': 'co2_emissions'})
            climate_df = climate_df.dropna(subset=['co2_emissions'])
            climate_df = climate_df[climate_df['co2_emissions'] > 0]
            climate_df = climate_df[(climate_df['year'] >= 2000) & (climate_df['year'] <= 2022)]
            climate_df['co2_emissions'] = climate_df['co2_emissions'] * 1000
            if len(climate_df) > 500:
                st.success("✅ Our World in Data에서 실시간 CO2 데이터를 성공적으로 로드했습니다!")
                return climate_df, True
    except Exception as e:
        st.warning(f"Our World in Data 로드 실패: {str(e)[:100]}...")
    st.warning("⚠️ 실시간 데이터 소스 연결 실패. 고품질 예시 데이터를 사용합니다.")
    return create_sample_climate_data(), False

def create_sample_climate_data():
    np.random.seed(42)
    years = list(range(2000, 2023))
    countries = ['USA', 'China', 'India', 'Germany', 'Japan', 'South Korea', 
                 'Brazil', 'Canada', 'Russia', 'Australia', 'United Kingdom', 
                 'France', 'Italy', 'Mexico', 'Indonesia']
    data = []
    base_emissions = {
        'USA': 5000000, 'China': 9000000, 'India': 2200000, 
        'Germany': 750000, 'Japan': 1150000, 'South Korea': 580000,
        'Brazil': 450000, 'Canada': 520000, 'Russia': 1650000, 
        'Australia': 410000, 'United Kingdom': 400000, 'France': 330000,
        'Italy': 320000, 'Mexico': 460000, 'Indonesia': 610000
    }
    for country in countries:
        base = base_emissions[country]
        for year in years:
            if country in ['China', 'India', 'Indonesia', 'Mexico']:
                trend = (year - 2000) * 0.025
            elif country in ['USA', 'Germany', 'Japan', 'United Kingdom', 'France']:
                trend = -(year - 2000) * 0.015
            else:
                trend = (year - 2000) * 0.005
            covid_effect = -0.1 if year == 2020 else 0
            noise = np.random.normal(0, 0.03)
            value = base * (1 + trend + covid_effect + noise)
            data.append({
                'country': country,
                'year': year,
                'co2_emissions': max(10000, value)
            })
    return pd.DataFrame(data)

@st.cache_data
def create_it_job_data():
    job_change_data = {
        '직업 분류': ['사라질 위험 직업'] * 6 + ['새롭게 부상하는 직업'] * 14,
        '직업명': [
            '기존 비효율 데이터센터 운영자', '전자폐기물 무관리 제조업체', 
            '고전력 소모 하드웨어 개발자', '비친환경 IT 제품 기획자',
            '탄소배출 무시 인프라 설계자', '비재생에너지 의존 시스템 관리자',
            '그린 데이터센터 아키텍트', '전자폐기물 순환경제 전문가',
            '저전력 반도체 설계 엔지니어', 'ESG IT 컨설턴트',
            '탄소중립 시스템 개발자', '신재생에너지 IT 통합 전문가',
            '친환경 AI/빅데이터 분석가', '디지털 탄소발자국 측정 전문가',
            '그린 클라우드 솔루션 아키텍트', '환경규제 대응 IT 전문가',
            '지속가능 IT 제품 디자이너', 'IT 에너지효율 최적화 전문가',
            '기후테크 소프트웨어 개발자', '환경감시 IoT 시스템 개발자'
        ],
        '전망 점수': [-8, -7, -6, -5, -7, -6, 9, 8, 8, 9, 8, 8, 9, 7, 8, 7, 7, 8, 8, 7],
        '연관 분야': [
            '데이터센터', '제조업', '하드웨어', 'IT제품', '인프라', '시스템',
            '그린IT', '순환경제', '반도체', 'ESG', '탄소중립', '신재생에너지',
            'AI/빅데이터', '탄소관리', '클라우드', '환경규제',
            '제품설계', '에너지효율', '기후테크', 'IoT'
        ],
        '카테고리': [
            '전통 IT', '전통 IT', '전통 IT', '전통 IT', '전통 IT', '전통 IT',
            '그린IT', '순환경제', '그린IT', 'ESG', '탄소중립', '에너지',
            '그린IT', '탄소관리', '그린IT', '규제대응',
            '그린IT', '에너지효율', '기후테크', '기후테크'
        ]
    }
    it_impact_data = {
        '영향 분야': ['에너지 소비', '탄소배출', '전자폐기물', '공급망 불안정', 
                      'ESG 경영', '친환경 규제', '기술혁신 촉진', '비즈니스 전략 변화'],
        '영향도 점수': [9, 8, 7, 6, 8, 7, 9, 8],
        '시급성': [9, 9, 6, 7, 7, 8, 8, 7],
        '대응 필요도': [9, 9, 7, 7, 8, 8, 9, 8]
    }
    skills_data = {
        '역량': ['분석적 사고', 'AI 및 빅데이터', '에너지 효율 설계', '친환경 기술 개발', 
                 '탄소 관리 능력', '순환경제 이해', 'ESG 경영 지식', '환경규제 대응능력',
                 '저전력 시스템 설계', '신재생에너지 통합'],
        '중요도 (%)': [85, 80, 75, 78, 70, 65, 68, 72, 73, 69],
        '성장률 (%)': [15, 25, 35, 32, 40, 28, 30, 25, 30, 33]
    }
    energy_trend_data = {
        # 연도를 2031년까지 포함하여 다른 항목들과 같이 10개로 수정
        '연도': list(range(2022, 2032)),
        '데이터센터 전력소모 (TWh)': [240, 280, 320, 380, 450, 500, 480, 460, 440, 420],
        '전체 IT산업 탄소배출 (%)': [3.2, 3.5, 3.8, 4.1, 4.2, 4.0, 3.7, 3.4, 3.1, 2.8],
        '친환경 IT 투자 (조원)': [15, 22, 35, 48, 65, 85, 110, 140, 175, 215]
    }
    climate_tech_solutions = {
        '솔루션': ['그린 데이터센터', '저전력 반도체', 'AI 에너지 최적화', 
                  '재생에너지 관리시스템', '탄소 추적 플랫폼'],
        '2024 시장규모 (억달러)': [120, 80, 60, 90, 40],
        '2030 예상규모 (억달러)': [450, 280, 250, 320, 180],
        '연평균 성장률 (%)': [24, 23, 26, 23, 28]
    }
    return (pd.DataFrame(job_change_data), pd.DataFrame(skills_data), 
            pd.DataFrame(energy_trend_data), pd.DataFrame(climate_tech_solutions),
            pd.DataFrame(it_impact_data))

# 데이터 로드
job_df, skills_df, energy_trend_df, climate_tech_df, impact_df = create_it_job_data()

# 메인 타이틀
st.title("🌍 기후위기와 IT직업 변화 종합 대시보드")
st.markdown("**실시간 기후 데이터와 미래 직업 전망을 통합 분석**")
st.markdown("---")

# 주요 인사이트 섹션
if show_insights:
    st.header("💡 주요 인사이트 및 미래 전망")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "데이터센터 전력소모 증가", 
            "2배",
            delta="2026년까지 (IEA)",
            help="국제에너지기구(IEA) 전망에 따른 데이터센터 전력 소비 증가율"
        )
    with col2:
        st.metric(
            "IT산업 온실가스 비중", 
            "2-4%",
            delta="전 세계 대비",
            help="IT 분야가 전체 온실가스 배출에서 차지하는 비중"
        )
    with col3:
        st.metric(
            "친환경 IT 투자", 
            "215조원",
            delta="2030년 예상",
            help="친환경 IT 기술 및 솔루션에 대한 글로벌 투자 규모"
        )
    with col4:
        st.metric(
            "그린 데이터센터 성장률", 
            "24%",
            delta="연평균 (2024-2030)",
            help="친환경 데이터센터 시장의 연평균 성장률"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🌍 기후위기가 IT산업에 미치는 영향**
        - **에너지 소비 급증**: 데이터센터, 클라우드, AI 인프라 확대
        - **탄소배출 증가**: IT분야 온실가스 배출 2-4% 차지
        - **전자폐기물 문제**: 짧은 제품 수명주기로 환경 문제 심화
        - **공급망 불안정**: 기후변화로 인한 원자재 가격 변동
        
        **📊 새로운 규제 환경**
        - EU RoHS, WEEE, 에코디자인 규제 강화
        - ESG 경영과 탄소중립 목표 필수화
        - 탄소국경세 등 글로벌 규제 확산
        """)
    
    with col2:
        st.markdown("""
        **🚀 IT업계의 대응 전략**
        - **그린 IT 기술**: 저전력 반도체, 효율적 냉각시스템
        - **신재생에너지**: 데이터센터의 재생에너지 전환
        - **AI 활용**: 에너지 최적화, 환경 감시, 탄소 관리
        - **순환경제**: 전자폐기물 재활용 및 수명 연장
        
        **🎯 미래 직업 전망**
        - 기존 비효율 시스템 관련 직업 쇠퇴
        - 그린IT, ESG, 탄소중립 전문가 급증
        - 친환경 기술 개발 및 규제 대응 전문가 필요
        """)
    
    st.subheader("🔮 2030년 IT 생태계 전망")
    
    future_outlook = {
        '분야': ['그린IT', '전통 IT', '기후테크', '에너지효율', 'ESG 테크'],
        '2024 점수': [70, 85, 60, 55, 50],
        '2030 예상 점수': [95, 65, 90, 85, 80],
        '변화율': [36, -24, 50, 55, 60],
        '변화율_절댓값': [36, 24, 50, 55, 60]
    }
    
    outlook_df = pd.DataFrame(future_outlook)
    
    fig = px.scatter(
        outlook_df,
        x='2024 점수',
        y='2030 예상 점수',
        size='변화율_절댓값',
        text='분야',
        title="IT 분야별 성장 전망 (2024 vs 2030) - PDF 분석 기반",
        labels={'2024 점수': '2024년 현재 수준', '2030 예상 점수': '2030년 예상 수준'},
        color='변화율',
        color_continuous_scale='RdYlGn',
        size_max=50,
        height=500,
        template=chart_template
    )
    
    fig.add_trace(go.Scatter(
        x=[0, 100],
        y=[0, 100],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='변화 없음 기준선',
        showlegend=True
    ))
    
    fig.update_traces(textposition="middle center")
    fig.update_layout(font=dict(family="Arial, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# 기후 데이터 섹션
if show_climate_data:
    st.markdown("---")
    st.header("🌡️ 전 세계 기후 변화 실시간 데이터")
    
    climate_df, is_real_data = load_climate_data()
    
    if not climate_df.empty:
        filtered_df = climate_df[
            (climate_df['year'] >= climate_year_range[0]) & 
            (climate_df['year'] <= climate_year_range[1])
        ]
        
        latest_year = filtered_df['year'].max()
        top_countries = filtered_df[filtered_df['year'] == latest_year].nlargest(top_countries_n, 'co2_emissions')['country'].tolist()
        filtered_df = filtered_df[filtered_df['country'].isin(top_countries)]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 연도별 CO2 배출량 추이")
            fig = px.line(
                filtered_df, 
                x='year', 
                y='co2_emissions', 
                color='country',
                title="CO2 배출량 추이 (킬로톤)",
                labels={'year': '연도', 'co2_emissions': 'CO2 배출량 (kt)', 'country': '국가'},
                template=chart_template,
                color_discrete_sequence=color_palette,
                height=chart_height
            )
            if show_data_labels:
                fig.update_traces(mode="lines+markers")
            fig.update_layout(font=dict(family="Arial, sans-serif"), legend_title_text="국가")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🥧 최근 연도 배출량 비중")
            latest_data = filtered_df[filtered_df['year'] == latest_year]
            fig = px.pie(
                latest_data, 
                values='co2_emissions', 
                names='country',
                title=f"{latest_year}년 CO2 배출량 비중",
                template=chart_template,
                color_discrete_sequence=color_palette,
                height=chart_height
            )
            if show_data_labels:
                fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

# IT 직업 변화 분석 섹션
if show_job_analysis:
    st.markdown("---")
    st.header("💼 기후위기와 IT 직업 변화 분석")
    
    if job_category_filter != "전체":
        job_df = job_df[job_df['카테고리'] == job_category_filter]
    
    if not show_declining_jobs:
        job_df = job_df[job_df['전망 점수'] > 0]
    
    filtered_energy_df = energy_trend_df[
        (energy_trend_df['연도'] >= prediction_years[0]) & 
        (energy_trend_df['연도'] <= prediction_years[1])
    ]
    
    st.subheader("🌡️ 기후위기가 IT산업에 미치는 영향 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            impact_df, x='영향도 점수', y='영향 분야', orientation='h',
            title="IT산업 분야별 기후위기 영향도", color='시급성',
            color_continuous_scale='Reds', height=chart_height,
            template=chart_template, text='영향도 점수'
        )
        fig.update_layout(font=dict(family="Arial, sans-serif"), yaxis={'categoryorder':'total ascending'})
        if show_data_labels:
            fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(
            impact_df, x='시급성', y='대응 필요도', size='영향도 점수',
            text='영향 분야', title="IT산업 대응 우선순위 매트릭스",
            color='영향도 점수', color_continuous_scale='viridis',
            height=chart_height, template=chart_template
        )
        fig.update_traces(textposition="middle center", textfont_size=9)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 IT 직업 변화 전망")
        fig = px.bar(
            job_df, x='전망 점수', y='직업명', color='직업 분류',
            orientation='h', title="IT 직업별 미래 전망 점수",
            color_discrete_map={'사라질 위험 직업': '#ff6b6b', '새롭게 부상하는 직업': '#4ecdc4'},
            height=chart_height, template=chart_template
        )
        fig.update_layout(font=dict(family="Arial, sans-serif"), yaxis={'categoryorder':'total ascending'})
        if show_data_labels:
            fig.update_traces(texttemplate='%{x}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 미래 핵심 역량")
        if skills_view == "중요도 vs 성장률":
            fig = px.scatter(
                skills_df, x='중요도 (%)', y='성장률 (%)',
                size=[15] * len(skills_df), text='역량',
                title="역량별 중요도 vs 성장률", color='성장률 (%)',
                color_continuous_scale='viridis', height=chart_height, template=chart_template
            )
            fig.update_traces(textposition="middle center")
            fig.update_layout(showlegend=False)
        elif skills_view == "막대 차트":
            fig = px.bar(
                skills_df, x='중요도 (%)', y='역량', orientation='h',
                title="미래 역량별 중요도", color='중요도 (%)',
                color_continuous_scale='Blues', height=chart_height, template=chart_template
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=skills_df['중요도 (%)'], theta=skills_df['역량'],
                fill='toself', name='중요도'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 90])),
                showlegend=True, title="미래 역량 레이더 차트",
                height=chart_height, template=chart_template
            )
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("⚡ IT산업 에너지 소비 & 친환경 투자 트렌드")

    fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]], subplot_titles=["IT산업 에너지 소비 vs 친환경 투자 (2022-2030)"])
    fig.add_trace(go.Scatter(x=filtered_energy_df['연도'], y=filtered_energy_df['데이터센터 전력소모 (TWh)'], mode='lines+markers', name='데이터센터 전력소모 (TWh)', line=dict(color='red', width=3), marker=dict(size=8)), secondary_y=False)
    fig.add_trace(go.Scatter(x=filtered_energy_df['연도'], y=filtered_energy_df['친환경 IT 투자 (조원)'], mode='lines+markers', name='친환경 IT 투자 (조원)', line=dict(color='green', width=3), marker=dict(size=8)), secondary_y=True)
    fig.update_xaxes(title_text="연도")
    fig.update_yaxes(title_text="전력소모 (TWh)", secondary_y=False)
    fig.update_yaxes(title_text="친환경 IT 투자 (조원)", secondary_y=True)
    fig.update_layout(title="IEA 예측: 2026년까지 데이터센터 전력 소모 2배 증가", font=dict(family="Arial, sans-serif"), hovermode='x unified', template=chart_template, height=500)
    st.plotly_chart(fig, use_container_width=True)

# 하단 정보
st.markdown("---")
footer_text = """
**📊 대시보드 정보**
- **실시간 기후 데이터**: Our World in Data GitHub Repository, World Bank Open Data API
- **IT 직업 분석**: World Economic Forum Future of Jobs Report 2025 + 업로드된 PDF 문서
- **PDF 문서 출처**: "기후위기가 IT산업에 어떻게 영향을 끼치는지" 분석 보고서
- **주요 출처**: 
  - [Our World in Data - CO2 Dataset](https://github.com/owid/co2-data)
  - [World Economic Forum Future of Jobs Report 2025](https://www.weforum.org/publications/the-future-of-jobs-report-2025/)
  - [국제에너지기구(IEA) 데이터센터 전력소비 전망](https://www.iea.org/)
  - [Salesforce 지속가능한 IT](https://www.salesforce.com/kr/hub/crm/sustainable-IT-digital-carbon-footprint/)
  - [삼성SDS Green IT 인사이트](https://www.samsungsds.com/kr/insights/it-220317.html)
- **업데이트**: 실시간 (기후 데이터), 2025년 1월 기준 (IT 직업 분석)
- **제작 환경**: GitHub Codespaces + Streamlit + Plotly
"""
st.markdown(footer_text)

with st.sidebar:
    st.markdown("---")
    st.subheader("📋 데이터 다운로드")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        csv1 = job_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 직업 변화", csv1, "it_job_changes_updated.csv", "text/csv", key="download1")
    
    with col2:
        csv2 = skills_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 핵심 역량", csv2, "future_skills_updated.csv", "text/csv", key="download2")
    
    with col3:
        csv3 = energy_trend_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 에너지 트렌드", csv3, "energy_trends.csv", "text/csv", key="download3")
    
    with col4:
        csv4 = climate_tech_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 기후테크", csv4, "climate_tech_solutions.csv", "text/csv", key="download4")
    
    with col5:
        csv5 = impact_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 영향도", csv5, "it_climate_impact.csv", "text/csv", key="download5")

st.subheader("")
