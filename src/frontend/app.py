import streamlit as st
import requests
import json

# --- Configuration ---
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- Helper Functions ---
def api_request(method, endpoint, **kwargs):
    """A wrapper for making API requests."""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        st.error(f"Response body: {e.response.text if e.response else 'No response'}")
        return None

# --- App Initialization ---
st.set_page_config(page_title="AI-HR Demo", layout="wide")

if 'stage' not in st.session_state:
    st.session_state.stage = 'start'
if 'candidate_data' not in st.session_state:
    st.session_state.candidate_data = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# --- Page Rendering ---

def render_start_page():
    st.title("Добро пожаловать в AI-HR Демо!")
    st.write("Эта демонстрация покажет работу MVP (Minimum Viable Product) AI-рекрутинговой воронки.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 HR: Создать вакансию", use_container_width=True):
            st.session_state.stage = 'stage_1_job_generation'
            st.rerun()
    with col2:
        if st.button("👤 Кандидат: Начать отбор", use_container_width=True):
            st.session_state.stage = 'stage_2_screening'
            st.rerun()

def render_stage_1_job_generation():
    st.title("Этап 1: AI-генерация вакансии")
    st.write("Заполните бриф, и AI сгенерирует профессиональную вакансию.")

    with st.form("job_generation_form"):
        col1, col2 = st.columns(2)

        with col1:
            job_title = st.text_input("Название должности *", placeholder="Менеджер по продажам B2B")
            company_name = st.text_input("Название компании *", placeholder="ТехноСофт")
            sales_segment = st.text_input("Сегмент продаж *", placeholder="B2B SaaS, средний бизнес")
            salary_range = st.text_input("Зарплата *", placeholder="80 000 - 150 000 руб + % от продаж")

        with col2:
            company_description = st.text_area("Описание компании", placeholder="IT-компания, разрабатывающая CRM-системы", height=68)
            work_format = st.selectbox("Формат работы", ["office", "remote", "hybrid"])
            sales_target = st.text_input("План продаж", placeholder="500 000 руб/мес выручки")
            additional_requirements = st.text_input("Доп. требования", placeholder="Опыт работы с CRM, английский")

        submitted = st.form_submit_button("🚀 Сгенерировать вакансию", use_container_width=True)

        if submitted:
            if not all([job_title, company_name, sales_segment, salary_range]):
                st.error("Заполните все обязательные поля (*)")
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
                        st.session_state.candidate_data['generated_job'] = response
                        st.session_state.stage = 'stage_1_result'
                        st.rerun()

def render_stage_1_result():
    st.title("✅ Вакансия сгенерирована!")

    job = st.session_state.candidate_data.get('generated_job', {})

    st.subheader(job.get('job_title_final', 'Вакансия'))
    st.caption(f"💰 {job.get('salary_display', '')}")

    st.markdown("### Описание")
    st.write(job.get('job_description', ''))

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📋 Требования")
        for req in job.get('requirements', []):
            st.write(f"• {req}")

        st.markdown("### ➕ Желательно")
        for nice in job.get('nice_to_have', []):
            st.write(f"• {nice}")

    with col2:
        st.markdown("### 🎁 Преимущества")
        for benefit in job.get('benefits', []):
            st.write(f"• {benefit}")

        st.markdown("### 🏷️ Теги")
        st.write(", ".join(job.get('tags', [])))

    st.markdown("### ❓ Скрининг-вопросы для кандидатов")
    for i, q in enumerate(job.get('screening_questions', []), 1):
        badge = "🚫 Deal-breaker" if q.get('deal_breaker') else ""
        st.write(f"{i}. {q.get('question', '')} ({q.get('type', '')}) {badge}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Сгенерировать заново", use_container_width=True):
            st.session_state.stage = 'stage_1_job_generation'
            st.rerun()
    with col2:
        if st.button("➡️ Перейти к отбору кандидатов", use_container_width=True):
            st.session_state.stage = 'stage_2_screening'
            st.rerun()

def render_stage_2_screening():
    st.title("Этап 2: Начальный скрининг")
    st.write("Ответьте на несколько ключевых вопросов.")
    
    with st.form("screening_form"):
        willing_to_cold_call = st.checkbox("Вы готовы совершать холодные звонки?")
        work_format = st.selectbox("Какой формат работы вам подходит?", ["office", "remote", "hybrid"])
        salary_expectation = st.number_input("Ваши зарплатные ожидания (в рублях)?", min_value=0, step=1000)
        
        submitted = st.form_submit_button("Отправить ответы")
        if submitted:
            answers = [
                {"question_id": "cold_calls", "answer": willing_to_cold_call},
                {"question_id": "work_format", "answer": work_format},
                {"question_id": "salary_expectation", "answer": salary_expectation}
            ]
            response = api_request("post", "/v1/screen/stage2_screening", json={"answers": answers})
            if response:
                st.session_state.candidate_data['stage2_response'] = response
                if response['passed']:
                    st.success(f"Вы прошли начальный скрининг! Детали: {response['details']}")
                    st.session_state.stage = 'stage_3_resume'
                else:
                    st.error(f"К сожалению, вы не прошли начальный скрининг. Детали: {response['details']}")
                    st.session_state.stage = 'end_fail'
                st.rerun()

def render_stage_3_resume():
    st.title("Этап 3: AI-анализ резюме")
    st.write("Вставьте текст вакансии и резюме для анализа.")

    with st.form("resume_form"):
        job_description = st.text_area("Текст вакансии", height=200, placeholder="Пример: Ищем менеджера по продажам в B2B SaaS...")
        resume_text = st.text_area("Текст резюме", height=400, placeholder="Пример: Иван Иванов, опыт работы в продажах 5 лет...")
        
        submitted = st.form_submit_button("Проанализировать резюме")
        if submitted:
            response = api_request("post", "/v1/screen/stage3_resume_scoring", json={
                "job_description": job_description,
                "resume_text": resume_text
            })
            if response:
                st.session_state.candidate_data['stage3_response'] = response
                st.subheader("Результаты анализа:")
                st.metric("Оценка соответствия", f"{response['score']}/100")
                st.info(f"**Резюме:** {response['summary']}")
                if response['red_flags']:
                    st.warning(f"**Красные флаги:** {', '.join(response['red_flags'])}")
                
                if response['score'] >= 65:
                    st.success("Резюме соответствует требованиям. Переходим к следующему этапу.")
                    st.session_state.stage = 'stage_6_chat'
                else:
                    st.error("Резюме не соответствует минимальным требованиям.")
                    st.session_state.stage = 'end_fail'
                st.rerun()

def render_stage_6_chat():
    st.title("Этап 6: Поведенческое AI-интервью")
    st.write("Вам будет задано несколько вопросов. Отвечайте честно и развернуто.")

    # Initialize chat
    if not st.session_state.chat_history:
        st.write("Начинаем чат...")
        response = api_request("post", "/v1/screen/stage6_behavioral_chat", json={"conversation": []})
        if response:
            st.session_state.chat_history = response['conversation']
            st.rerun()
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    # Final assessment display
    if 'assessment' in st.session_state and st.session_state.assessment:
        st.subheader("Интервью завершено. Результаты оценки:")
        st.json(st.session_state.assessment)
        st.session_state.stage = 'end_success'
        st.button("Завершить")
        return

    # User input
    if prompt := st.chat_input("Ваш ответ"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.spinner("AI анализирует ваш ответ..."):
            response = api_request("post", "/v1/screen/stage6_behavioral_chat", json={"conversation": st.session_state.chat_history})
            if response:
                st.session_state.chat_history = response['conversation']
                if response.get('assessment'):
                    st.session_state.assessment = response['assessment']
                st.rerun()

def render_end_page(success=True):
    if success:
        st.balloons()
        st.title("Поздравляем! Вы успешно прошли все этапы отбора.")
        st.write("Сводная информация по кандидату:")
        st.json(st.session_state.candidate_data)
    else:
        st.error("Процесс отбора завершен.")
        st.write("К сожалению, на одном из этапов кандидат не прошел отбор.")
        st.write("Данные последнего этапа:")
        st.json(st.session_state.candidate_data.get(f"stage{st.session_state.stage[5]}_response", {}))

# --- Main App Logic ---
page = st.session_state.get('stage', 'start')

if page == 'start':
    render_start_page()
elif page == 'stage_1_job_generation':
    render_stage_1_job_generation()
elif page == 'stage_1_result':
    render_stage_1_result()
elif page == 'stage_2_screening':
    render_stage_2_screening()
elif page == 'stage_3_resume':
    render_stage_3_resume()
elif page == 'stage_6_chat':
    render_stage_6_chat()
elif page == 'end_success':
    render_end_page(success=True)
elif page == 'end_fail':
    render_end_page(success=False)
