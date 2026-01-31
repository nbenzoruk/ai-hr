"""
AI-HR: Панель HR-специалиста
Создание вакансий и управление кандидатами
"""
import streamlit as st
import requests
import os
import json
import re
import io
from datetime import datetime

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- Validation Functions ---
def validate_salary(salary_str: str) -> tuple[bool, str]:
    """
    Validates salary input. Accepts:
    - Single numbers: "100000", "100 000"
    - Ranges: "80000-150000", "80 000 - 150 000", "от 80000 до 150000"
    - With currency/bonus: "100000 руб", "80000-150000 + %"

    Returns: (is_valid, error_message)
    """
    if not salary_str or not salary_str.strip():
        return False, "Укажите зарплату"

    # Remove extra spaces
    cleaned = ' '.join(salary_str.split())

    # Check for at least one number in the string
    numbers = re.findall(r'\d[\d\s]*\d|\d', cleaned)
    if not numbers:
        return False, "Зарплата должна содержать числа. Например: '100000' или '80000-150000'"

    # Extract all numeric values (removing spaces within numbers)
    numeric_values = []
    for num_str in numbers:
        num_clean = num_str.replace(' ', '')
        if num_clean.isdigit():
            numeric_values.append(int(num_clean))

    if not numeric_values:
        return False, "Не удалось распознать числовые значения в зарплате"

    # Check reasonable range (1000 to 10,000,000)
    for val in numeric_values:
        if val < 1000:
            return False, f"Значение {val} слишком маленькое. Возможно, вы имели в виду {val * 1000}?"
        if val > 10000000:
            return False, f"Значение {val} слишком большое. Проверьте правильность ввода"

    return True, ""

def generate_candidate_pdf(candidate: dict) -> bytes:
    """Generate PDF report for a candidate. Uses simple text format if reportlab not available."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, spaceAfter=20)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceBefore=15, spaceAfter=10)
        normal_style = styles['Normal']

        story = []

        # Title
        story.append(Paragraph(f"Профиль кандидата: {candidate.get('name', 'Без имени')}", title_style))
        story.append(Spacer(1, 0.5*cm))

        # Status
        status_map = {'completed': 'Прошёл отбор', 'rejected': 'Отклонён', 'in_progress': 'В процессе'}
        status = status_map.get(candidate.get('status', ''), candidate.get('status', ''))
        story.append(Paragraph(f"<b>Статус:</b> {status}", normal_style))
        story.append(Paragraph(f"<b>Дата подачи:</b> {candidate.get('created_at', 'Н/Д')}", normal_style))
        story.append(Spacer(1, 0.5*cm))

        # Resume section
        resume = candidate.get('resume', {})
        if resume:
            story.append(Paragraph("Анализ резюме", heading_style))
            story.append(Paragraph(f"<b>Оценка:</b> {resume.get('score', 'Н/Д')}/100", normal_style))
            story.append(Paragraph(f"<b>Статус:</b> {'Пройден' if resume.get('passed') else 'Не пройден'}", normal_style))
            if resume.get('summary'):
                story.append(Paragraph(f"<b>Комментарий AI:</b> {resume['summary']}", normal_style))
            story.append(Spacer(1, 0.3*cm))

        # Motivation section
        motivation = candidate.get('motivation', {})
        if motivation:
            story.append(Paragraph("Мотивация", heading_style))
            story.append(Paragraph(f"<b>Основной мотиватор:</b> {motivation.get('primary_motivation', 'Н/Д')}", normal_style))
            story.append(Paragraph(f"<b>Вторичный мотиватор:</b> {motivation.get('secondary_motivation', 'Н/Д')}", normal_style))
            story.append(Spacer(1, 0.3*cm))

        # Cognitive test section
        cognitive = candidate.get('cognitive', {})
        if cognitive:
            story.append(Paragraph("Когнитивный тест", heading_style))
            story.append(Paragraph(f"<b>Результат:</b> {cognitive.get('score', 0)}/{cognitive.get('total', 3)}", normal_style))
            story.append(Paragraph(f"<b>Статус:</b> {'Пройден' if cognitive.get('passed') else 'Не пройден'}", normal_style))
            story.append(Spacer(1, 0.3*cm))

        # Interview section
        interview = candidate.get('interview', {})
        if interview:
            story.append(Paragraph("Поведенческое интервью", heading_style))

            competencies = [
                ('Проактивность', interview.get('proactivity', 0)),
                ('Честность', interview.get('honesty', 0)),
                ('Устойчивость', interview.get('resilience', 0)),
                ('Структурность', interview.get('structure', 0)),
                ('Мотивация', interview.get('motivation', 0)),
            ]

            for name, score in competencies:
                story.append(Paragraph(f"<b>{name}:</b> {score}/10", normal_style))

            if interview.get('final_summary'):
                story.append(Spacer(1, 0.2*cm))
                story.append(Paragraph(f"<b>Заключение AI:</b> {interview['final_summary']}", normal_style))

        # Footer
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Сгенерировано AI-HR Panel",
            ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=colors.gray)))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    except ImportError:
        # Fallback to simple text file if reportlab not installed
        status_map = {'completed': 'Прошёл отбор', 'rejected': 'Отклонён', 'in_progress': 'В процессе'}
        status_text = status_map.get(candidate.get('status', ''), candidate.get('status', ''))
        separator = '=' * 50
        line = '-' * 30

        text_content = f"""
ПРОФИЛЬ КАНДИДАТА: {candidate.get('name', 'Без имени')}
{separator}

Статус: {status_text}
Дата подачи: {candidate.get('created_at', 'Н/Д')}

АНАЛИЗ РЕЗЮМЕ
{line}
"""
        resume = candidate.get('resume', {})
        if resume:
            text_content += f"Оценка: {resume.get('score', 'Н/Д')}/100\n"
            text_content += f"Статус: {'Пройден' if resume.get('passed') else 'Не пройден'}\n"
            if resume.get('summary'):
                text_content += f"Комментарий: {resume['summary']}\n"

        text_content += f"\nМОТИВАЦИЯ\n{line}\n"
        motivation = candidate.get('motivation', {})
        if motivation:
            text_content += f"Основной мотиватор: {motivation.get('primary_motivation', 'Н/Д')}\n"
            text_content += f"Вторичный мотиватор: {motivation.get('secondary_motivation', 'Н/Д')}\n"

        text_content += f"\nКОГНИТИВНЫЙ ТЕСТ\n{line}\n"
        cognitive = candidate.get('cognitive', {})
        if cognitive:
            text_content += f"Результат: {cognitive.get('score', 0)}/{cognitive.get('total', 3)}\n"

        text_content += f"\nИНТЕРВЬЮ\n{line}\n"
        interview = candidate.get('interview', {})
        if interview:
            text_content += f"Проактивность: {interview.get('proactivity', 0)}/10\n"
            text_content += f"Честность: {interview.get('honesty', 0)}/10\n"
            text_content += f"Устойчивость: {interview.get('resilience', 0)}/10\n"
            text_content += f"Структурность: {interview.get('structure', 0)}/10\n"
            text_content += f"Мотивация: {interview.get('motivation', 0)}/10\n"
            if interview.get('final_summary'):
                text_content += f"\nЗаключение: {interview['final_summary']}\n"

        text_content += f"\n{separator}\nСгенерировано AI-HR Panel\n"

        return text_content.encode('utf-8')

# --- Helper Functions ---
def api_request(method, endpoint, **kwargs):
    """A wrapper for making API requests."""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен.")
        st.caption(f"URL: {url}")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Сервер не отвечает. Попробуйте ещё раз.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 500:
            st.error("⚠️ Ошибка на сервере. Возможно, проблема с AI-провайдером.")
            try:
                detail = e.response.json().get('detail', '')
                if detail:
                    st.caption(f"Детали: {detail}")
            except:
                pass
        else:
            st.error(f"❌ Ошибка API: {e.response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка запроса: {e}")
        return None

# --- App Initialization ---
st.set_page_config(
    page_title="HR Panel | AI-HR",
    page_icon="🎯",
    layout="wide"
)

if 'hr_page' not in st.session_state:
    st.session_state.hr_page = 'dashboard'
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'current_job' not in st.session_state:
    st.session_state.current_job = None
# Демо-данные кандидатов (в реальности будут из БД)
if 'demo_candidates' not in st.session_state:
    st.session_state.demo_candidates = [
        {
            "id": 1,
            "name": "Иван Петров",
            "status": "completed",
            "screening": {"passed": True},
            "resume": {"passed": True, "score": 78, "summary": "Опытный менеджер с хорошим track record"},
            "motivation": {"primary_motivation": "Деньги", "secondary_motivation": "Карьера"},
            "cognitive": {"score": 3, "total": 3, "passed": True},
            "interview": {
                "proactivity": 8,
                "honesty": 9,
                "resilience": 7,
                "structure": 8,
                "motivation": 9,
                "final_summary": "Сильный кандидат с хорошей мотивацией"
            },
            "personality": {
                "persistence": 85,
                "stress_resistance": 72,
                "energy": 78,
                "sociability": 90,
                "honesty": 88,
                "teamwork": 65,
                "routine_tolerance": 70,
                "sales_fit_score": 79,
                "summary": "Сильные стороны: persistence, sociability, honesty. Общая оценка для продаж: 79/100",
                "red_flags": []
            },
            "sales": {
                "cold_calling_readiness": 85,
                "objection_handling": 78,
                "closing_ability": 82,
                "value_selling": 75,
                "hunter_vs_farmer": 80,
                "money_orientation": 90,
                "overall_sales_score": 81,
                "recommendation": "Сильный охотник с высокой денежной мотивацией. Рекомендуется для B2B активных продаж.",
                "concerns": []
            },
            "created_at": "2024-01-20 14:30"
        },
        {
            "id": 2,
            "name": "Мария Сидорова",
            "status": "rejected",
            "rejection_stage": "resume",
            "screening": {"passed": True},
            "resume": {"passed": False, "score": 45, "summary": "Мало релевантного опыта"},
            "created_at": "2024-01-20 15:45"
        },
        {
            "id": 3,
            "name": "Алексей Козлов",
            "status": "in_progress",
            "current_stage": "personality",
            "screening": {"passed": True},
            "resume": {"passed": True, "score": 82, "summary": "Хороший опыт в B2B продажах, знание CRM"},
            "motivation": {"primary_motivation": "Интерес к задачам", "secondary_motivation": "Обучение"},
            "cognitive": {"score": 2, "total": 3, "passed": True},
            "interview": {
                "proactivity": 7,
                "honesty": 8,
                "resilience": 6,
                "structure": 7,
                "motivation": 8,
                "final_summary": "Мотивированный кандидат, требуется проверка стрессоустойчивости"
            },
            "personality": {
                "persistence": 60,
                "stress_resistance": 45,
                "energy": 70,
                "sociability": 75,
                "honesty": 82,
                "teamwork": 80,
                "routine_tolerance": 55,
                "sales_fit_score": 63,
                "summary": "Зоны развития: stress_resistance, routine_tolerance. Общая оценка для продаж: 63/100",
                "red_flags": ["Низкая стрессоустойчивость - риск выгорания"]
            },
            "created_at": "2024-01-20 16:00"
        }
    ]

# --- Breadcrumbs ---
def render_breadcrumbs():
    """Render breadcrumb navigation."""
    page = st.session_state.get('hr_page', 'dashboard')
    page_titles = {
        'dashboard': 'Dashboard',
        'create_job': 'Создать вакансию',
        'candidates': 'Кандидаты',
        'offers': 'Офферы',
        'onboarding': 'Онбординг',
        'settings': 'Настройки'
    }

    current_page = page_titles.get(page, 'Dashboard')

    # Create breadcrumb trail
    if page == 'dashboard':
        st.caption("🏠 AI-HR Panel")
    else:
        col1, col2 = st.columns([3, 9])
        with col1:
            if st.button("🏠 Dashboard", key="breadcrumb_home", help="Вернуться на главную"):
                st.session_state.hr_page = 'dashboard'
                st.rerun()
        with col2:
            st.caption(f" › **{current_page}**")

# --- Custom CSS and JavaScript for better UX ---
def inject_custom_css():
    """Inject custom CSS for better active button indication."""
    st.markdown("""
    <style>
    /* Make primary buttons more visible in sidebar */
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #ff4b4b !important;
        color: white !important;
        border: 2px solid #ff4b4b !important;
        font-weight: bold !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: transparent !important;
        color: #262730 !important;
        border: 1px solid #e0e0e0 !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #f0f0f0 !important;
        border-color: #ff4b4b !important;
    }
    </style>
    """, unsafe_allow_html=True)

def inject_keyboard_shortcuts():
    """Inject JavaScript for keyboard shortcuts using components.html."""
    import streamlit.components.v1 as components
    components.html("""
    <script>
    // Keyboard shortcuts: Cmd+K / Ctrl+K to focus search
    const parentDoc = window.parent.document;
    parentDoc.addEventListener('keydown', function(e) {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            // Find search input in parent document
            const inputs = parentDoc.querySelectorAll('input[type="text"]');
            for (let input of inputs) {
                if (input.placeholder && (input.placeholder.includes('Имя') || input.placeholder.includes('кандидат'))) {
                    input.focus();
                    input.select();
                    break;
                }
            }
        }
    });
    </script>
    """, height=0)

# --- Sidebar Navigation ---
def render_sidebar():
    with st.sidebar:
        st.title("🎯 HR Panel")
        st.divider()

        st.subheader("📍 Навигация")

        if st.button("📊 Dashboard", use_container_width=True,
                     type="primary" if st.session_state.hr_page == 'dashboard' else "secondary"):
            st.session_state.hr_page = 'dashboard'
            st.rerun()

        if st.button("➕ Создать вакансию", use_container_width=True,
                     type="primary" if st.session_state.hr_page == 'create_job' else "secondary"):
            st.session_state.hr_page = 'create_job'
            st.rerun()

        if st.button("👥 Кандидаты", use_container_width=True,
                     type="primary" if st.session_state.hr_page == 'candidates' else "secondary"):
            st.session_state.hr_page = 'candidates'
            st.rerun()

        if st.button("📝 Офферы", use_container_width=True,
                     type="primary" if st.session_state.hr_page == 'offers' else "secondary"):
            st.session_state.hr_page = 'offers'
            st.rerun()

        if st.button("🚀 Онбординг", use_container_width=True,
                     type="primary" if st.session_state.hr_page == 'onboarding' else "secondary"):
            st.session_state.hr_page = 'onboarding'
            st.rerun()

        if st.button("⚙️ Настройки", use_container_width=True,
                     type="primary" if st.session_state.hr_page == 'settings' else "secondary"):
            st.session_state.hr_page = 'settings'
            st.rerun()

        if st.button("🔧 Admin", use_container_width=True,
                     type="primary" if st.session_state.hr_page == 'admin' else "secondary"):
            st.session_state.hr_page = 'admin'
            st.rerun()

        st.divider()

        # Быстрая статистика
        st.subheader("📈 Статистика")
        candidates = st.session_state.demo_candidates
        total = len(candidates)
        completed = len([c for c in candidates if c['status'] == 'completed'])
        rejected = len([c for c in candidates if c['status'] == 'rejected'])
        in_progress = len([c for c in candidates if c['status'] == 'in_progress'])

        col1, col2 = st.columns(2)
        col1.metric("Всего", total)
        col2.metric("Завершили", completed)

        col1, col2 = st.columns(2)
        col1.metric("В процессе", in_progress)
        col2.metric("Отклонены", rejected)

        st.divider()
        st.caption("AI-HR Panel v0.3")

# --- Page Rendering ---

def render_dashboard():
    render_breadcrumbs()
    st.title("📊 Dashboard")

    # KPI метрики
    candidates = st.session_state.demo_candidates
    total = len(candidates)
    completed = len([c for c in candidates if c['status'] == 'completed'])
    rejected = len([c for c in candidates if c['status'] == 'rejected'])
    in_progress = len([c for c in candidates if c['status'] == 'in_progress'])

    conversion = (completed / total * 100) if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📥 Всего кандидатов", total, "+3 за неделю")
    col2.metric("✅ Прошли отбор", completed)
    col3.metric("🔄 В процессе", in_progress)
    col4.metric("📈 Конверсия", f"{conversion:.0f}%")

    st.divider()

    # Последние кандидаты
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("👥 Последние кандидаты")
        for candidate in candidates[:5]:
            status_icons = {
                'completed': '✅',
                'rejected': '❌',
                'in_progress': '🔄'
            }
            status_icon = status_icons.get(candidate['status'], '❓')

            with st.container():
                col_name, col_status, col_date = st.columns([2, 1, 1])
                # Clickable candidate name
                if col_name.button(
                    f"👤 {candidate['name']}",
                    key=f"dash_candidate_{candidate['id']}",
                    help="Нажмите для просмотра профиля"
                ):
                    st.session_state.hr_page = 'candidates'
                    st.session_state.selected_candidate_id = candidate['id']
                    st.rerun()
                col_status.write(status_icon)
                col_date.caption(candidate.get('created_at', ''))

    with col2:
        st.subheader("📋 Активные вакансии")
        if st.session_state.jobs:
            for job in st.session_state.jobs:
                st.write(f"• {job.get('job_title_final', 'Без названия')}")
        else:
            st.info("Нет активных вакансий")
            if st.button("➕ Создать первую вакансию"):
                st.session_state.hr_page = 'create_job'
                st.rerun()

    st.divider()

    # Воронка отбора
    st.subheader("🎯 Воронка отбора")

    # Подсчёт по этапам
    screening_passed = len([c for c in candidates if c.get('screening', {}).get('passed')])
    resume_passed = len([c for c in candidates if c.get('resume', {}).get('passed')])
    cognitive_passed = len([c for c in candidates if c.get('cognitive', {}).get('passed')])
    interview_completed = completed

    funnel_data = {
        "Скрининг": screening_passed,
        "Резюме": resume_passed,
        "Когнитивный тест": cognitive_passed,
        "Интервью завершено": interview_completed
    }

    cols = st.columns(len(funnel_data))
    for i, (stage, count) in enumerate(funnel_data.items()):
        with cols[i]:
            st.metric(stage, count)
            if i > 0:
                prev_count = list(funnel_data.values())[i-1]
                if prev_count > 0:
                    conversion = count / prev_count * 100
                    st.caption(f"↓ {conversion:.0f}%")

def render_create_job():
    render_breadcrumbs()
    st.title("➕ Создать вакансию")
    st.write("Заполните бриф, и AI сгенерирует профессиональную вакансию.")

    with st.form("job_creation_form"):
        col1, col2 = st.columns(2)

        with col1:
            job_title = st.text_input(
                "Название должности *",
                placeholder="Менеджер по продажам B2B",
                help="Например: Менеджер по продажам, Sales Manager, Account Executive"
            )
            company_name = st.text_input(
                "Название компании *",
                placeholder="ТехноСофт",
                help="Официальное название компании-работодателя"
            )
            sales_segment = st.text_input(
                "Сегмент продаж *",
                placeholder="B2B SaaS, средний бизнес",
                help="Целевой сегмент: B2B, B2C, Enterprise, SMB и т.д."
            )
            salary_range = st.text_input(
                "Зарплата *",
                placeholder="80 000 - 150 000 руб + % от продаж",
                help="Формат: число, диапазон или 'от X до Y'. Можно добавить бонусы"
            )

        with col2:
            company_description = st.text_area(
                "Описание компании",
                placeholder="IT-компания, разрабатывающая CRM-системы",
                height=68,
                help="Краткое описание для привлечения кандидатов"
            )
            work_format = st.selectbox(
                "Формат работы",
                ["office", "remote", "hybrid"],
                format_func=lambda x: {"office": "🏢 Офис", "remote": "🏠 Удалённо", "hybrid": "🔄 Гибрид"}[x],
                help="Офис, удалённо или гибридный формат"
            )
            sales_target = st.text_input(
                "План продаж",
                placeholder="500 000 руб/мес выручки",
                help="Ожидаемый объём продаж или KPI"
            )
            additional_requirements = st.text_input(
                "Доп. требования",
                placeholder="Опыт работы с CRM, английский язык",
                help="Специфические требования: навыки, языки, сертификаты"
            )

        submitted = st.form_submit_button("🚀 Сгенерировать вакансию", type="primary", use_container_width=True)

        if submitted:
            # Validate required fields
            if not all([job_title, company_name, sales_segment, salary_range]):
                st.error("❌ Заполните все обязательные поля (*)")
            else:
                # Validate salary format
                is_valid, error_msg = validate_salary(salary_range)
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                else:
                    with st.spinner("AI генерирует вакансию..."):
                        response = api_request("post", "/v1/jobs/generate", json={
                            "job_title": job_title,
                            "company_name": company_name,
                            "company_description": company_description or None,
                            "sales_segment": sales_segment,
                            "salary_range": salary_range,
                            "sales_target": sales_target or None,
                            "work_format": work_format,
                            "additional_requirements": additional_requirements or None
                        })
                        if response:
                            st.session_state.current_job = response
                            st.session_state.jobs.append(response)
                            st.toast("✅ Вакансия успешно создана!", icon="✅")
                            st.rerun()

    # Показываем созданную вакансию
    if st.session_state.current_job:
        st.divider()
        render_job_preview(st.session_state.current_job)

def render_job_preview(job):
    """Render a job posting preview."""
    st.subheader(f"📋 {job.get('job_title_final', 'Вакансия')}")
    st.caption(f"💰 {job.get('salary_display', '')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Описание")
        st.write(job.get('job_description', ''))

        st.markdown("### Требования")
        for req in job.get('requirements', []):
            st.write(f"• {req}")

    with col2:
        st.markdown("### Желательно")
        for nice in job.get('nice_to_have', []):
            st.write(f"• {nice}")

        st.markdown("### Преимущества")
        for benefit in job.get('benefits', []):
            st.write(f"• {benefit}")

    st.markdown("### 🏷️ Теги")
    tags = job.get('tags', [])
    if tags:
        st.write(" | ".join([f"`{tag}`" for tag in tags]))

    st.markdown("### ❓ Скрининг-вопросы")
    for i, q in enumerate(job.get('screening_questions', []), 1):
        deal_breaker = "🚨" if q.get('deal_breaker') else ""
        st.write(f"{i}. {q.get('question', '')} [{q.get('type', '')}] {deal_breaker}")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Копировать текст"):
            # В Streamlit нет прямого доступа к буферу обмена
            st.info("Функция копирования будет добавлена")
    with col2:
        if st.button("🔄 Сгенерировать заново"):
            st.session_state.current_job = None
            st.rerun()
    with col3:
        if st.button("✅ Опубликовать"):
            st.success("Вакансия опубликована! (демо)")

def render_candidates():
    render_breadcrumbs()
    st.title("👥 Кандидаты")

    # Check if we came from dashboard with a selected candidate
    pre_search = ""
    if 'selected_candidate_id' in st.session_state:
        selected_id = st.session_state.selected_candidate_id
        # Find candidate name by ID
        for c in st.session_state.demo_candidates:
            if c['id'] == selected_id:
                pre_search = c['name']
                break
        # Clear the selection
        del st.session_state.selected_candidate_id

    # Фильтры
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Статус",
            ["Все", "Прошли отбор", "В процессе", "Отклонены"],
            help="Фильтр по статусу прохождения"
        )
    with col2:
        sort_by = st.selectbox(
            "Сортировка",
            ["По дате (новые)", "По дате (старые)", "По имени"],
            help="Порядок отображения кандидатов"
        )
    with col3:
        search = st.text_input("🔍 Поиск", value=pre_search, placeholder="Имя кандидата...", help="Поиск по имени")

    st.divider()

    # Фильтрация кандидатов
    candidates = st.session_state.demo_candidates.copy()

    if status_filter == "Прошли отбор":
        candidates = [c for c in candidates if c['status'] == 'completed']
    elif status_filter == "В процессе":
        candidates = [c for c in candidates if c['status'] == 'in_progress']
    elif status_filter == "Отклонены":
        candidates = [c for c in candidates if c['status'] == 'rejected']

    if search:
        candidates = [c for c in candidates if search.lower() in c['name'].lower()]

    # Список кандидатов
    for candidate in candidates:
        render_candidate_card(candidate)

def render_candidate_card(candidate):
    """Render a detailed candidate card."""
    status_info = {
        'completed': ('✅ Прошёл отбор', 'success'),
        'rejected': ('❌ Отклонён', 'error'),
        'in_progress': ('🔄 В процессе', 'info')
    }
    status_text, status_type = status_info.get(candidate['status'], ('❓', 'warning'))

    with st.expander(f"**{candidate['name']}** — {status_text}"):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**ID:** {candidate['id']}")
            st.markdown(f"**Дата:** {candidate.get('created_at', 'Н/Д')}")

            if candidate['status'] == 'rejected':
                stage_names = {
                    'screening': 'Скрининг',
                    'resume': 'Анализ резюме',
                    'cognitive': 'Когнитивный тест'
                }
                rejection_stage = candidate.get('rejection_stage', 'unknown')
                st.error(f"Отклонён на этапе: {stage_names.get(rejection_stage, rejection_stage)}")

            if candidate['status'] == 'in_progress':
                st.info(f"Текущий этап: {candidate.get('current_stage', 'Н/Д')}")

        with col2:
            # Быстрые метрики
            if candidate.get('resume', {}).get('score'):
                st.metric("Резюме", f"{candidate['resume']['score']}/100")
            if candidate.get('cognitive', {}).get('score'):
                st.metric("Когн. тест", f"{candidate['cognitive']['score']}/{candidate['cognitive']['total']}")

        st.divider()

        # Детальная информация по этапам
        tabs = st.tabs(["📋 Скрининг", "📄 Резюме", "💡 Мотивация", "🧠 Тест", "💬 Интервью", "🎭 Личность", "💼 Сейлз"])

        with tabs[0]:
            screening = candidate.get('screening', {})
            if screening:
                st.write(f"**Статус:** {'✅ Пройден' if screening.get('passed') else '❌ Не пройден'}")
            else:
                st.write("Данные отсутствуют")

        with tabs[1]:
            resume = candidate.get('resume', {})
            if resume:
                st.metric("Оценка соответствия", f"{resume.get('score', 'Н/Д')}/100")
                st.write(f"**Статус:** {'✅ Пройден' if resume.get('passed') else '❌ Не пройден'}")
                if resume.get('summary'):
                    st.info(f"**AI-резюме:** {resume['summary']}")
            else:
                st.write("Данные отсутствуют")

        with tabs[2]:
            motivation = candidate.get('motivation', {})
            if motivation:
                col1, col2 = st.columns(2)
                col1.metric("Основной мотиватор", motivation.get('primary_motivation', 'Н/Д'))
                col2.metric("Вторичный мотиватор", motivation.get('secondary_motivation', 'Н/Д'))
            else:
                st.write("Данные отсутствуют")

        with tabs[3]:
            cognitive = candidate.get('cognitive', {})
            if cognitive:
                st.metric("Результат", f"{cognitive.get('score', 0)} из {cognitive.get('total', 3)}")
                st.write(f"**Статус:** {'✅ Пройден' if cognitive.get('passed') else '❌ Не пройден'}")
            else:
                st.write("Данные отсутствуют")

        with tabs[4]:
            interview = candidate.get('interview', {})
            if interview:
                st.markdown("#### Оценки по компетенциям:")
                col1, col2, col3 = st.columns(3)
                col1.metric("Проактивность", f"{interview.get('proactivity', 0)}/10")
                col2.metric("Честность", f"{interview.get('honesty', 0)}/10")
                col3.metric("Устойчивость", f"{interview.get('resilience', 0)}/10")

                col1, col2 = st.columns(2)
                col1.metric("Структурность", f"{interview.get('structure', 0)}/10")
                col2.metric("Мотивация", f"{interview.get('motivation', 0)}/10")

                if interview.get('final_summary'):
                    st.success(f"**AI-заключение:** {interview['final_summary']}")
            else:
                st.write("Данные отсутствуют")

        with tabs[5]:
            personality = candidate.get('personality', {})
            if personality:
                st.markdown("#### Личностный профиль (ТУЛС)")

                # Визуализация профиля
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Настойчивость", f"{personality.get('persistence', 0)}/100")
                    st.metric("Стрессоустойчивость", f"{personality.get('stress_resistance', 0)}/100")
                    st.metric("Энергия", f"{personality.get('energy', 0)}/100")
                    st.metric("Общительность", f"{personality.get('sociability', 0)}/100")
                with col2:
                    st.metric("Честность", f"{personality.get('honesty', 0)}/100")
                    st.metric("Командность", f"{personality.get('teamwork', 0)}/100")
                    st.metric("Готовность к рутине", f"{personality.get('routine_tolerance', 0)}/100")
                    st.metric("Sales Fit Score", f"{personality.get('sales_fit_score', 0)}/100")

                if personality.get('summary'):
                    st.info(f"**Резюме:** {personality['summary']}")

                red_flags = personality.get('red_flags', [])
                if red_flags:
                    st.warning("**Красные флаги:**")
                    for flag in red_flags:
                        st.write(f"• {flag}")
            else:
                st.write("Данные отсутствуют")

        with tabs[6]:
            sales = candidate.get('sales', {})
            if sales:
                st.markdown("#### Сейлз-компетенции")

                col1, col2, col3 = st.columns(3)
                col1.metric("Холодные звонки", f"{sales.get('cold_calling_readiness', 0)}/100")
                col2.metric("Работа с возражениями", f"{sales.get('objection_handling', 0)}/100")
                col3.metric("Закрытие сделок", f"{sales.get('closing_ability', 0)}/100")

                col1, col2, col3 = st.columns(3)
                col1.metric("Value selling", f"{sales.get('value_selling', 0)}/100")
                col2.metric("Hunter/Farmer", f"{sales.get('hunter_vs_farmer', 0)}/100")
                col3.metric("Денежная мотивация", f"{sales.get('money_orientation', 0)}/100")

                st.metric("Общая сейлз-оценка", f"{sales.get('overall_sales_score', 0)}/100")

                if sales.get('recommendation'):
                    st.success(f"**Рекомендация:** {sales['recommendation']}")

                concerns = sales.get('concerns', [])
                if concerns:
                    st.warning("**Зоны риска:**")
                    for concern in concerns:
                        st.write(f"• {concern}")
            else:
                st.write("Данные отсутствуют")

        # Действия
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📧 Написать", key=f"email_{candidate['id']}", help="Отправить email кандидату"):
                st.info("Функция отправки email будет добавлена")
        with col2:
            # PDF Export
            pdf_data = generate_candidate_pdf(candidate)
            file_ext = "pdf" if pdf_data[:4] == b'%PDF' else "txt"
            st.download_button(
                "📥 Экспорт PDF",
                data=pdf_data,
                file_name=f"candidate_{candidate['id']}_{candidate['name'].replace(' ', '_')}.{file_ext}",
                mime="application/pdf" if file_ext == "pdf" else "text/plain",
                key=f"pdf_{candidate['id']}",
                help="Скачать профиль кандидата"
            )
        with col3:
            if st.button("📋 Interview Guide", key=f"guide_{candidate['id']}", help="Сгенерировать гайд для интервью"):
                with st.spinner("Генерируем AI-гайд..."):
                    guide = api_request("post", "/v1/screen/stage12_interview_guide", json={"candidate_id": candidate['id']})
                    if guide:
                        st.session_state[f'interview_guide_{candidate["id"]}'] = guide
                        st.rerun()
        with col4:
            if candidate['status'] == 'completed':
                if st.button("📝 Оффер", key=f"offer_{candidate['id']}", help="Создать оффер"):
                    st.session_state.offer_candidate = candidate
                    st.session_state.hr_page = 'offers'
                    st.rerun()

        # Показываем Interview Guide если есть
        guide_key = f'interview_guide_{candidate["id"]}'
        if guide_key in st.session_state:
            guide = st.session_state[guide_key]
            st.divider()
            st.markdown("### 📋 AI Interview Guide")

            st.markdown("#### Executive Summary")
            st.info(guide.get('executive_summary', ''))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### ✅ Сильные стороны")
                for s in guide.get('strengths', []):
                    st.write(f"• {s}")
            with col2:
                st.markdown("#### ⚠️ Зоны риска")
                for c in guide.get('concerns', []):
                    st.write(f"• {c}")

            st.markdown("#### ❓ Рекомендуемые вопросы")
            for i, q in enumerate(guide.get('recommended_questions', []), 1):
                st.write(f"{i}. {q}")

            st.markdown("#### 🚨 Deal-breaker сигналы")
            for s in guide.get('deal_breaker_signals', []):
                st.error(f"• {s}")

            rec_colors = {'strong_yes': 'success', 'yes': 'success', 'maybe': 'warning', 'no': 'error'}
            rec_labels = {'strong_yes': '✅✅ Настоятельно рекомендуем', 'yes': '✅ Рекомендуем', 'maybe': '🤔 Возможно', 'no': '❌ Не рекомендуем'}
            rec = guide.get('hiring_recommendation', 'maybe')
            getattr(st, rec_colors.get(rec, 'info'))(f"**Рекомендация:** {rec_labels.get(rec, rec)}\n\n{guide.get('recommendation_reasoning', '')}")

# === Admin Section ===

def render_admin():
    """Admin panel for managing prompts and system settings."""
    render_breadcrumbs()
    st.title("🔧 Admin Panel")

    # Admin sub-navigation
    admin_tab = st.radio(
        "Раздел",
        ["AI Промпты", "Системные настройки", "Этапы воронки"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.divider()

    if admin_tab == "AI Промпты":
        render_admin_prompts()
    elif admin_tab == "Системные настройки":
        render_admin_settings()
    elif admin_tab == "Этапы воронки":
        render_admin_stages()


def render_admin_prompts():
    """Manage AI prompts."""
    st.subheader("🤖 AI Промпты")
    st.info("Редактируйте промпты для AI без изменения кода. Изменения применяются сразу.")

    # Fetch prompts from API
    try:
        response = requests.get(f"{BACKEND_URL}/v1/admin/prompts", timeout=10)
        if response.status_code == 200:
            prompts = response.json()
        else:
            st.error(f"Ошибка загрузки промптов: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        st.error(f"Не удалось подключиться к API: {e}")
        return

    if not prompts:
        st.warning("Промпты не найдены. Перезапустите бэкенд для seed данных.")
        return

    # Prompt selector
    prompt_keys = {p['key']: p['name'] for p in prompts}
    selected_key = st.selectbox(
        "Выберите промпт для редактирования",
        options=list(prompt_keys.keys()),
        format_func=lambda x: f"{prompt_keys[x]} ({x})"
    )

    # Find selected prompt
    selected_prompt = next((p for p in prompts if p['key'] == selected_key), None)

    if selected_prompt:
        st.divider()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Ключ:** `{selected_prompt['key']}`")
            st.markdown(f"**Версия:** {selected_prompt['version']}")

        with col2:
            st.markdown(f"**Обновлён:** {selected_prompt['updated_at'][:10]}")

        # Edit form
        with st.form(f"edit_prompt_{selected_key}"):
            new_name = st.text_input("Название", value=selected_prompt['name'])

            new_description = st.text_area(
                "Описание",
                value=selected_prompt.get('description') or '',
                height=60
            )

            new_system_message = st.text_area(
                "System Message (опционально)",
                value=selected_prompt.get('system_message') or '',
                height=80,
                help="Системное сообщение для AI. Задаёт роль и контекст."
            )

            new_prompt_template = st.text_area(
                "Шаблон промпта",
                value=selected_prompt['prompt_template'],
                height=300,
                help="Используйте {переменная} для подстановки значений."
            )

            # Show variables
            variables = selected_prompt.get('template_variables', [])
            if variables:
                st.markdown(f"**Переменные:** `{', '.join(variables)}`")

            new_temperature = st.slider(
                "Температура",
                min_value=0.0,
                max_value=1.0,
                value=float(selected_prompt.get('temperature') or 0.7),
                step=0.1,
                help="0 = детерминированный, 1 = максимально креативный"
            )

            col1, col2 = st.columns(2)

            with col1:
                save_btn = st.form_submit_button("💾 Сохранить", type="primary", use_container_width=True)

            with col2:
                test_btn = st.form_submit_button("🧪 Тест", use_container_width=True)

            if save_btn:
                update_data = {
                    "name": new_name,
                    "description": new_description if new_description else None,
                    "system_message": new_system_message if new_system_message else None,
                    "prompt_template": new_prompt_template,
                    "temperature": new_temperature
                }

                try:
                    resp = requests.put(
                        f"{BACKEND_URL}/v1/admin/prompts/{selected_key}",
                        json=update_data,
                        timeout=10
                    )
                    if resp.status_code == 200:
                        st.success(f"✅ Промпт '{new_name}' сохранён! Версия: {resp.json()['version']}")
                        st.rerun()
                    else:
                        st.error(f"Ошибка сохранения: {resp.text}")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

        # Test section (outside form)
        st.divider()
        st.subheader("🧪 Тестирование промпта")

        with st.expander("Тестовые данные", expanded=False):
            test_variables = {}
            for var in variables:
                test_variables[var] = st.text_area(
                    var,
                    value=f"[Тестовое значение для {var}]",
                    height=80,
                    key=f"test_var_{var}"
                )

            if st.button("▶️ Запустить тест", type="primary"):
                with st.spinner("AI обрабатывает..."):
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/v1/admin/prompts/{selected_key}/test",
                            json={"variables": test_variables},
                            timeout=60
                        )
                        if resp.status_code == 200:
                            result = resp.json()
                            if result.get('error'):
                                st.error(f"Ошибка: {result['error']}")
                            else:
                                st.success("Тест выполнен!")
                                st.markdown("**Отрендеренный промпт:**")
                                st.code(result.get('prompt_rendered', '')[:1000] + "...", language="markdown")
                                st.markdown("**Ответ AI:**")
                                st.json(result.get('ai_response', ''))
                        else:
                            st.error(f"Ошибка: {resp.text}")
                    except Exception as e:
                        st.error(f"Ошибка: {e}")


def render_admin_settings():
    """Manage system settings."""
    st.subheader("⚙️ Системные настройки")
    st.info("Глобальные настройки системы. Влияют на все новые вакансии и кандидатов.")

    # Fetch current settings
    try:
        response = requests.get(f"{BACKEND_URL}/v1/admin/settings", timeout=10)
        if response.status_code == 200:
            settings = response.json()
        else:
            st.error(f"Ошибка загрузки настроек: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        st.error(f"Не удалось подключиться к API: {e}")
        return

    with st.form("admin_settings"):
        st.markdown("### 🤖 AI Настройки")

        col1, col2 = st.columns(2)

        with col1:
            ai_temperature = st.slider(
                "Температура AI",
                min_value=0.0,
                max_value=1.0,
                value=float(settings.get('ai_temperature', 0.7)),
                step=0.1,
                help="Влияет на креативность ответов AI"
            )

        with col2:
            ai_model = st.text_input(
                "Модель AI (опционально)",
                value=settings.get('ai_model_name') or '',
                help="Оставьте пустым для использования модели по умолчанию"
            )

        st.divider()
        st.markdown("### 📊 Пороги по умолчанию")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            resume_threshold = st.number_input(
                "Резюме (мин. балл)",
                min_value=0,
                max_value=100,
                value=settings.get('default_resume_threshold', 65),
                help="Минимальный балл для прохождения"
            )

        with col2:
            cognitive_pass = st.number_input(
                "Когнитивный тест",
                min_value=1,
                max_value=3,
                value=settings.get('default_cognitive_pass', 2),
                help="Минимум правильных ответов из 3"
            )

        with col3:
            personality_threshold = st.number_input(
                "Личность (мин.)",
                min_value=0,
                max_value=100,
                value=settings.get('default_personality_threshold', 40),
                help="Порог для красных флагов"
            )

        with col4:
            sales_threshold = st.number_input(
                "Sales (мин.)",
                min_value=0,
                max_value=100,
                value=settings.get('default_sales_threshold', 40),
                help="Минимальный sales score"
            )

        st.divider()
        st.markdown("### 📋 Критерии скрининга по умолчанию")

        screening = settings.get('default_screening_criteria', {})

        col1, col2, col3 = st.columns(3)

        with col1:
            cold_calls = st.checkbox(
                "Требовать холодные звонки",
                value=screening.get('cold_calls', {}).get('expected', True)
            )

        with col2:
            work_format = st.selectbox(
                "Формат работы",
                ["office", "remote", "hybrid", "any"],
                index=["office", "remote", "hybrid", "any"].index(
                    screening.get('work_format', {}).get('expected', 'office')
                )
            )

        with col3:
            max_salary = st.number_input(
                "Макс. зарплата",
                min_value=0,
                max_value=500000,
                value=screening.get('salary_expectation', {}).get('max_allowed', 60000),
                step=5000
            )

        if st.form_submit_button("💾 Сохранить настройки", type="primary", use_container_width=True):
            update_data = {
                "ai_temperature": ai_temperature,
                "ai_model_name": ai_model if ai_model else None,
                "default_resume_threshold": resume_threshold,
                "default_cognitive_pass": cognitive_pass,
                "default_personality_threshold": personality_threshold,
                "default_sales_threshold": sales_threshold,
                "default_screening_criteria": {
                    "cold_calls": {"expected": cold_calls},
                    "work_format": {"expected": work_format},
                    "salary_expectation": {"max_allowed": max_salary}
                }
            }

            try:
                resp = requests.put(
                    f"{BACKEND_URL}/v1/admin/settings",
                    json=update_data,
                    timeout=10
                )
                if resp.status_code == 200:
                    st.success("✅ Настройки сохранены!")
                    st.rerun()
                else:
                    st.error(f"Ошибка: {resp.text}")
            except Exception as e:
                st.error(f"Ошибка: {e}")


def render_admin_stages():
    """Manage stage definitions (Phase 2 - basic view)."""
    st.subheader("📋 Этапы воронки")
    st.info("Управление этапами рекрутинговой воронки. (Функционал в разработке)")

    # Fetch stages from API
    try:
        response = requests.get(f"{BACKEND_URL}/v1/admin/stages", timeout=10)
        if response.status_code == 200:
            stages = response.json()
        else:
            st.warning("Этапы ещё не настроены. Функционал будет добавлен в следующей версии.")
            stages = []
    except requests.exceptions.RequestException:
        stages = []

    if stages:
        for stage in stages:
            with st.expander(f"{stage['icon']} {stage['name']} ({stage['key']})"):
                st.write(f"**Тип:** {stage['stage_type']}")
                st.write(f"**Блокирующий:** {'Да' if stage['is_blocking'] else 'Нет'}")
                st.write(f"**Критерии:** {stage['pass_criteria']}")
    else:
        # Show default stages (hardcoded for now)
        default_stages = [
            ("📋", "Скрининг", "screening", "form", True),
            ("📄", "Анализ резюме", "resume", "ai_analysis", True),
            ("💡", "Мотивация", "motivation", "form", False),
            ("🧠", "Когнитивный тест", "cognitive", "test", True),
            ("💬", "AI Интервью", "interview", "chat", False),
            ("🎭", "Личность", "personality", "test", True),
            ("💼", "Sales-кейсы", "sales", "ai_analysis", True),
            ("📊", "Результат", "result", "summary", False),
        ]

        st.markdown("**Текущие этапы (по умолчанию):**")

        for icon, name, key, stage_type, blocking in default_stages:
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            col1.write(icon)
            col2.write(name)
            col3.write(f"`{key}`")
            col4.write("🔴 Блокирующий" if blocking else "🟢 Не блокирующий")

        st.divider()
        st.info("💡 В следующей версии вы сможете включать/выключать этапы и настраивать их пороги.")


def render_settings():
    render_breadcrumbs()
    st.title("⚙️ Настройки")

    st.subheader("📋 Критерии скрининга")
    st.info("Эти критерии используются для автоматического отсева кандидатов на первом этапе.")

    with st.form("screening_settings"):
        col1, col2 = st.columns(2)

        with col1:
            cold_calls_required = st.checkbox("Требовать готовность к холодным звонкам", value=True)
            work_format = st.selectbox(
                "Требуемый формат работы",
                ["office", "remote", "hybrid", "any"],
                format_func=lambda x: {
                    "office": "🏢 Только офис",
                    "remote": "🏠 Только удалённо",
                    "hybrid": "🔄 Только гибрид",
                    "any": "✅ Любой"
                }[x]
            )

        with col2:
            max_salary = st.number_input(
                "Максимальная зарплата (₽)",
                min_value=0,
                max_value=500000,
                value=60000,
                step=5000
            )
            min_resume_score = st.slider(
                "Минимальный балл резюме",
                min_value=0,
                max_value=100,
                value=65
            )

        if st.form_submit_button("💾 Сохранить настройки", type="primary"):
            st.toast("✅ Настройки скрининга сохранены!", icon="✅")

    st.divider()

    st.subheader("🤖 Настройки AI")
    st.info("Настройки AI-модели для генерации и анализа.")

    with st.form("ai_settings"):
        temperature = st.slider(
            "Температура (креативность)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Выше = более креативные ответы, ниже = более предсказуемые"
        )

        if st.form_submit_button("💾 Сохранить настройки AI"):
            st.toast("✅ Настройки AI сохранены!", icon="🤖")

    st.divider()

    st.subheader("🔗 Интеграции")
    st.write("Подключение внешних сервисов (в разработке)")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📧 Email (SMTP)", disabled=True)
    with col2:
        st.button("📊 Google Sheets", disabled=True)
    with col3:
        st.button("💬 Telegram Bot", disabled=True)


def render_offers():
    """Render offers management page."""
    render_breadcrumbs()
    st.title("📝 Управление офферами")

    # Форма создания оффера
    if 'offer_candidate' in st.session_state:
        candidate = st.session_state.offer_candidate
        st.subheader(f"Создать оффер для: {candidate['name']}")

        with st.form("create_offer_form"):
            col1, col2 = st.columns(2)
            with col1:
                salary = st.number_input("Зарплата (₽)", min_value=30000, max_value=500000, value=80000, step=5000)
                start_date = st.date_input("Дата выхода")
            with col2:
                probation = st.selectbox("Испытательный срок", [1, 2, 3, 6], index=2, format_func=lambda x: f"{x} мес.")
                additional = st.text_area("Дополнительные условия", placeholder="Бонусы, ДМС, опционы...")

            if st.form_submit_button("📝 Создать оффер", type="primary", use_container_width=True):
                response = api_request("post", "/v1/offers", json={
                    "candidate_id": candidate['id'],
                    "salary_offered": salary,
                    "start_date": start_date.isoformat(),
                    "probation_period_months": probation,
                    "additional_terms": additional if additional else None
                })
                if response:
                    st.toast("✅ Оффер создан!", icon="📝")
                    del st.session_state.offer_candidate
                    st.rerun()

        if st.button("← Отмена"):
            del st.session_state.offer_candidate
            st.rerun()

        st.divider()

    # Список офферов
    st.subheader("📋 Все офферы")

    # Демо-данные офферов
    if 'demo_offers' not in st.session_state:
        st.session_state.demo_offers = [
            {
                "id": 1,
                "candidate_name": "Иван Петров",
                "job_title": "Менеджер по продажам B2B",
                "salary_offered": 95000,
                "start_date": "2024-02-01",
                "status": "sent",
                "created_at": "2024-01-22"
            }
        ]

    status_filter = st.selectbox("Фильтр по статусу", ["Все", "Черновик", "Отправлен", "Принят", "Отклонён"])

    offers = st.session_state.demo_offers
    status_map = {"Черновик": "draft", "Отправлен": "sent", "Принят": "accepted", "Отклонён": "rejected"}
    if status_filter != "Все":
        offers = [o for o in offers if o['status'] == status_map.get(status_filter)]

    if not offers:
        st.info("Нет офферов")
    else:
        for offer in offers:
            status_icons = {"draft": "📝", "sent": "📤", "accepted": "✅", "rejected": "❌", "expired": "⏰"}
            status_labels = {"draft": "Черновик", "sent": "Отправлен", "accepted": "Принят", "rejected": "Отклонён", "expired": "Истёк"}

            with st.expander(f"{status_icons.get(offer['status'], '❓')} {offer['candidate_name']} — {offer['job_title']}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Зарплата", f"{offer['salary_offered']:,} ₽")
                col2.metric("Дата выхода", offer['start_date'])
                col3.metric("Статус", status_labels.get(offer['status'], offer['status']))

                st.caption(f"Создан: {offer['created_at']}")

                col1, col2, col3 = st.columns(3)
                if offer['status'] == 'draft':
                    if col1.button("📤 Отправить", key=f"send_offer_{offer['id']}"):
                        offer['status'] = 'sent'
                        st.toast("📤 Оффер отправлен!", icon="✅")
                        st.rerun()
                if offer['status'] == 'sent':
                    if col1.button("✅ Принят", key=f"accept_offer_{offer['id']}"):
                        offer['status'] = 'accepted'
                        st.toast("🎉 Кандидат принял оффер!", icon="🎉")
                        st.rerun()
                    if col2.button("❌ Отклонён", key=f"reject_offer_{offer['id']}"):
                        offer['status'] = 'rejected'
                        st.toast("😔 Оффер отклонён", icon="❌")
                        st.rerun()


def render_onboarding():
    """Render onboarding tracking page."""
    render_breadcrumbs()
    st.title("🚀 Онбординг")

    # Демо-данные онбординга
    if 'demo_onboarding' not in st.session_state:
        st.session_state.demo_onboarding = [
            {
                "candidate_id": 1,
                "candidate_name": "Иван Петров",
                "job_title": "Менеджер по продажам B2B",
                "start_date": "2024-02-01",
                "status": "onboarding",
                "checklist": [
                    {"id": "docs", "title": "Документы оформлены", "completed": True},
                    {"id": "equipment", "title": "Оборудование выдано", "completed": True},
                    {"id": "access", "title": "Доступы настроены", "completed": True},
                    {"id": "intro_meeting", "title": "Встреча с командой", "completed": True},
                    {"id": "product_training", "title": "Обучение по продукту", "completed": False},
                    {"id": "sales_training", "title": "Тренинг по продажам", "completed": False},
                    {"id": "first_calls", "title": "Первые звонки", "completed": False},
                    {"id": "first_meeting", "title": "Первая встреча с клиентом", "completed": False},
                    {"id": "week1_review", "title": "Ревью 1 недели", "completed": False},
                    {"id": "month1_review", "title": "Ревью 1 месяца", "completed": False},
                ],
                "metrics": {"calls_made": 45, "meetings_scheduled": 3, "deals_in_pipeline": 2, "revenue_generated": 0}
            }
        ]

    # KPI метрики по онбордингу
    onboardings = st.session_state.demo_onboarding
    col1, col2, col3 = st.columns(3)
    col1.metric("Всего на онбординге", len(onboardings))
    col2.metric("На испытательном", len([o for o in onboardings if o['status'] == 'probation']))
    col3.metric("Завершили онбординг", len([o for o in onboardings if o['status'] == 'completed']))

    st.divider()

    # Список сотрудников на онбординге
    for onb in onboardings:
        completed_items = sum(1 for item in onb['checklist'] if item['completed'])
        total_items = len(onb['checklist'])
        progress = completed_items / total_items

        status_labels = {"onboarding": "🎓 Онбординг", "probation": "⏳ Испытательный", "completed": "✅ Завершён"}

        with st.expander(f"**{onb['candidate_name']}** — {onb['job_title']} | {status_labels.get(onb['status'], onb['status'])}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### 📋 Чек-лист онбординга")
                st.progress(progress, text=f"{completed_items}/{total_items} выполнено ({progress*100:.0f}%)")

                for item in onb['checklist']:
                    col_check, col_text = st.columns([1, 10])
                    checked = col_check.checkbox("", value=item['completed'], key=f"onb_{onb['candidate_id']}_{item['id']}")
                    if checked != item['completed']:
                        item['completed'] = checked
                        st.rerun()
                    col_text.write(f"{'~~' if item['completed'] else ''}{item['title']}{'~~' if item['completed'] else ''}")

            with col2:
                st.markdown("#### 📊 Метрики")
                metrics = onb['metrics']
                st.metric("Звонков", metrics['calls_made'])
                st.metric("Встреч назначено", metrics['meetings_scheduled'])
                st.metric("Сделок в воронке", metrics['deals_in_pipeline'])
                st.metric("Выручка", f"{metrics['revenue_generated']:,.0f} ₽")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Дата выхода:** {onb['start_date']}")
            with col2:
                if onb['status'] == 'onboarding':
                    if st.button("✅ Перевести на испытательный", key=f"probation_{onb['candidate_id']}"):
                        onb['status'] = 'probation'
                        st.toast("Сотрудник переведён на испытательный срок!", icon="✅")
                        st.rerun()
                elif onb['status'] == 'probation':
                    if st.button("🎉 Завершить онбординг", key=f"complete_{onb['candidate_id']}"):
                        onb['status'] = 'completed'
                        st.toast("🎉 Онбординг успешно завершён!", icon="🎉")
                        st.rerun()


# --- Main App Logic ---
inject_custom_css()
inject_keyboard_shortcuts()
render_sidebar()

page = st.session_state.get('hr_page', 'dashboard')

if page == 'dashboard':
    render_dashboard()
elif page == 'create_job':
    render_create_job()
elif page == 'candidates':
    render_candidates()
elif page == 'offers':
    render_offers()
elif page == 'onboarding':
    render_onboarding()
elif page == 'settings':
    render_settings()
elif page == 'admin':
    render_admin()
