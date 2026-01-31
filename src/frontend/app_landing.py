"""
AI-HR Landing Page
Single entry point with product info and portal selection
"""
import streamlit as st
import os

# Page config
st.set_page_config(
    page_title="AI-HR | AI-powered Recruitment",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# URLs for portals (Railway production or localhost)
CANDIDATE_URL = os.getenv("CANDIDATE_PORTAL_URL", "https://frontend-candidate-production.up.railway.app")
HR_URL = os.getenv("HR_PANEL_URL", "https://frontend-hr-production.up.railway.app")

# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Center content */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }

    /* Hero section */
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        color: #1a1a2e;
    }

    .hero-subtitle {
        font-size: 1.3rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }

    /* Feature cards */
    .feature-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #FF6B35;
    }

    .feature-title {
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.3rem;
    }

    .feature-desc {
        color: #666;
        font-size: 0.9rem;
    }

    /* Portal buttons */
    .portal-button {
        display: block;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        text-align: center;
        text-decoration: none;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 0.5rem 0;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .portal-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }

    .candidate-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }

    .hr-btn {
        background: linear-gradient(135deg, #FF6B35 0%, #f7931e 100%);
        color: white !important;
    }

    /* Stats */
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF6B35;
    }

    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }

    /* Funnel diagram */
    .funnel-stage {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.3rem 0;
        border-left: 3px solid #FF6B35;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown('<p class="hero-title">🤖 AI-HR</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">AI-powered рекрутинговая воронка для автоматизации отбора кандидатов</p>', unsafe_allow_html=True)

st.markdown("---")

# Portal Selection
st.markdown("### Выберите портал")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f'''
    <a href="{CANDIDATE_URL}" target="_blank" class="portal-button candidate-btn">
        👤 Я кандидат
        <br><small style="font-weight: 400; font-size: 0.8rem;">Пройти отбор на вакансию</small>
    </a>
    ''', unsafe_allow_html=True)

with col2:
    st.markdown(f'''
    <a href="{HR_URL}" target="_blank" class="portal-button hr-btn">
        💼 Я HR / Рекрутер
        <br><small style="font-weight: 400; font-size: 0.8rem;">Управление вакансиями</small>
    </a>
    ''', unsafe_allow_html=True)

st.markdown("---")

# Features
st.markdown("### Возможности платформы")

features = [
    ("🎯", "14 этапов отбора", "Скрининг, тесты, AI-интервью, оценка компетенций"),
    ("🤖", "AI-скоринг резюме", "Автоматический анализ соответствия кандидата вакансии"),
    ("🧠", "Когнитивные тесты", "Оценка логического мышления и внимательности"),
    ("💬", "AI-интервью", "Поведенческое интервью с виртуальным рекрутером"),
    ("📊", "Детальная аналитика", "Профиль кандидата, красные флаги, рекомендации"),
    ("🎮", "Геймификация", "Бейджи, XP, прогресс-бар для вовлечения кандидатов"),
]

for icon, title, desc in features:
    st.markdown(f'''
    <div class="feature-card">
        <div class="feature-title">{icon} {title}</div>
        <div class="feature-desc">{desc}</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown("---")

# Funnel Stages
st.markdown("### Этапы воронки")

stages = [
    "1️⃣ Скрининг-вопросы",
    "2️⃣ Загрузка резюме → AI-анализ",
    "3️⃣ Мотивационный опрос",
    "4️⃣ Когнитивный тест (3 задачи)",
    "5️⃣ Поведенческое интервью с AI",
    "6️⃣ Личностный профиль",
    "7️⃣ Сейлз-блок (для менеджеров продаж)",
    "8️⃣ Финальный отчёт для HR",
]

col1, col2 = st.columns(2)
for i, stage in enumerate(stages):
    target = col1 if i < 4 else col2
    with target:
        st.markdown(f'<div class="funnel-stage">{stage}</div>', unsafe_allow_html=True)

st.markdown("---")

# Tech Stack
st.markdown("### Технологии")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Backend**")
    st.caption("FastAPI, Python 3.11, SQLAlchemy")
with col2:
    st.markdown("**Frontend**")
    st.caption("Streamlit")
with col3:
    st.markdown("**AI**")
    st.caption("OpenAI GPT / Google Gemini")

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.85rem;">
    <p>Created by <a href="https://github.com/nbenzoruk" target="_blank">Nikita Benzoruk</a></p>
    <p>🚀 Deployed on Railway | 📖 <a href="https://github.com/nbenzoruk/ai-hr" target="_blank">GitHub</a></p>
</div>
""", unsafe_allow_html=True)
