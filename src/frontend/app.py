import streamlit as st
import requests
import json

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"

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
    if st.button("Начать процесс отбора"):
        st.session_state.stage = 'stage_2_screening'
        st.experimental_rerun()

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
                st.button("Продолжить") # Button to force rerun

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
                st.button("Продолжить")

def render_stage_6_chat():
    st.title("Этап 6: Поведенческое AI-интервью")
    st.write("Вам будет задано несколько вопросов. Отвечайте честно и развернуто.")

    # Initialize chat
    if not st.session_state.chat_history:
        st.write("Начинаем чат...")
        response = api_request("post", "/v1/screen/stage6_behavioral_chat", json={"conversation": []})
        if response:
            st.session_state.chat_history = response['conversation']
            st.experimental_rerun()
    
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
                st.experimental_rerun()

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
