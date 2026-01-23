import streamlit as st
import requests
import json
import os

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

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
st.set_page_config(page_title="AI-HR Demo", layout="wide")

if 'stage' not in st.session_state:
    st.session_state.stage = 'start'
if 'candidate_data' not in st.session_state:
    st.session_state.candidate_data = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'assessment' not in st.session_state:
    st.session_state.assessment = None

# --- Stage Progress Configuration ---
STAGES_ORDER = [
    ('start', '🏠 Старт'),
    ('stage_1_job_generation', '📝 1. Создание вакансии'),
    ('stage_1_result', '✅ 1. Вакансия готова'),
    ('stage_2_screening', '📋 2. Скрининг'),
    ('stage_3_resume', '📄 3. Анализ резюме'),
    ('stage_4_motivation', '💡 4. Мотивация'),
    ('stage_5_cognitive_test', '🧠 5. Когнитивный тест'),
    ('stage_6_chat', '💬 6. AI-интервью'),
    ('end_success', '🎉 Успех!'),
    ('end_fail', '❌ Не прошёл'),
]

def get_stage_index(stage_key):
    """Get the index of current stage for progress calculation."""
    for i, (key, _) in enumerate(STAGES_ORDER):
        if key == stage_key:
            return i
    return 0

def render_sidebar():
    """Render sidebar with progress and controls."""
    with st.sidebar:
        st.title("🎯 AI-HR Demo")
        st.divider()

        # Progress indicator
        current_stage = st.session_state.get('stage', 'start')
        current_idx = get_stage_index(current_stage)
        total_stages = len(STAGES_ORDER) - 2  # Exclude end states
        progress = min(current_idx / total_stages, 1.0)

        st.subheader("📊 Прогресс")
        st.progress(progress)

        # Stage list
        st.markdown("**Этапы:**")
        for i, (key, label) in enumerate(STAGES_ORDER):
            if key in ('end_success', 'end_fail'):
                continue
            if i < current_idx:
                st.markdown(f"~~{label}~~ ✓")
            elif i == current_idx:
                st.markdown(f"**→ {label}**")
            else:
                st.markdown(f"<span style='color: gray'>{label}</span>", unsafe_allow_html=True)

        st.divider()

        # Reset button
        if st.button("🔄 Начать заново", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # Demo hints toggle
        st.divider()
        st.session_state.show_hints = st.checkbox("💡 Показать подсказки", value=st.session_state.get('show_hints', False))

        st.divider()
        st.caption("AI-HR MVP v0.1")

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

        submitted = st.form_submit_button("Сгенерировать вакансию", use_container_width=True)

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
    st.title("Вакансия сгенерирована!")

    job = st.session_state.candidate_data.get('generated_job', {})

    st.subheader(job.get('job_title_final', 'Вакансия'))
    st.caption(f"Зарплата: {job.get('salary_display', '')}")

    st.markdown("### Описание")
    st.write(job.get('job_description', ''))

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Требования")
        for req in job.get('requirements', []):
            st.write(f"- {req}")

        st.markdown("### Желательно")
        for nice in job.get('nice_to_have', []):
            st.write(f"- {nice}")

    with col2:
        st.markdown("### Преимущества")
        for benefit in job.get('benefits', []):
            st.write(f"- {benefit}")

        st.markdown("### Теги")
        st.write(", ".join(job.get('tags', [])))

    st.markdown("### Скрининг-вопросы для кандидатов")
    for i, q in enumerate(job.get('screening_questions', []), 1):
        badge = " (deal-breaker)" if q.get('deal_breaker') else ""
        st.write(f"{i}. {q.get('question', '')} [{q.get('type', '')}]{badge}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Сгенерировать заново", use_container_width=True):
            st.session_state.stage = 'stage_1_job_generation'
            st.rerun()
    with col2:
        if st.button("Перейти к отбору кандидатов", use_container_width=True):
            st.session_state.stage = 'stage_2_screening'
            st.rerun()

def render_stage_2_screening():
    st.title("Этап 2: Начальный скрининг")
    st.write("Ответьте на несколько ключевых вопросов.")

    if st.session_state.get('show_hints'):
        st.info("""
        💡 **Подсказка для демо:** Чтобы пройти этот этап:
        - Холодные звонки: **ДА** (обязательно!)
        - Формат работы: **office** (только офис)
        - Зарплата: **≤ 60 000** руб (не больше)
        """)

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

    if st.session_state.get('show_hints'):
        st.info("""
        💡 **Подсказка для демо:** Нужно набрать **≥65 баллов**.

        **Пример вакансии:**
        > Ищем менеджера по продажам B2B. Опыт работы от 2 лет, знание CRM, навыки переговоров.

        **Пример резюме:**
        > Иван Петров. Опыт в B2B продажах 5 лет. Работал с CRM Bitrix24. Выполнял план на 120%. Провёл 200+ успешных сделок.
        """)

    with st.form("resume_form"):
        job_description = st.text_area("Текст вакансии", height=200, placeholder="Пример: Ищем менеджера по продажам в B2B SaaS...")
        resume_text = st.text_area("Текст резюме", height=400, placeholder="Пример: Иван Иванов, опыт работы в продажах 5 лет...")
        submitted = st.form_submit_button("Проанализировать резюме")
        if submitted:
            with st.spinner("AI анализирует резюме..."):
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
                    st.session_state.stage = 'stage_4_motivation'
                else:
                    st.error("Резюме не соответствует минимальным требованиям.")
                    st.session_state.stage = 'end_fail'
                st.rerun()

def render_stage_4_motivation():
    st.title("Этап 4: Опрос по мотивации")
    st.write("Ответьте на несколько коротких вопросов, чтобы мы лучше поняли ваши карьерные цели.")

    if st.session_state.get('show_hints'):
        st.info("""
        💡 **Подсказка для демо:** Этот этап не отсеивает — просто классифицирует мотивацию.

        **Примеры ответов:**
        - Мотивация: *"Высокий доход и возможность влиять на результат"*
        - Смена работы: *"Хочу больше ответственности и роста"*
        - KPI: *"Отношусь положительно, люблю измеримые цели"*
        """)

    with st.form("motivation_form"):
        answer_motivation = st.text_area("Что вас мотивирует в работе больше всего?", placeholder="Например: возможность влиять на продукт, высокий доход, карьерный рост...")
        answer_reason_for_leaving = st.text_area("Почему вы решили сменить работу?", placeholder="Например: ищу новые вызовы, не было возможностей для роста...")
        answer_kpi = st.text_area("Как вы относитесь к работе по KPI и планам продаж?", placeholder="Например: положительно, это помогает фокусироваться на результате...")
        submitted = st.form_submit_button("Отправить на анализ")
        if submitted:
            with st.spinner("AI анализирует ваши мотиваторы..."):
                response = api_request("post", "/v1/screen/stage4_motivation_survey", json={
                    "answer_motivation": answer_motivation,
                    "answer_reason_for_leaving": answer_reason_for_leaving,
                    "answer_kpi": answer_kpi
                })
            if response:
                st.session_state.candidate_data['stage4_response'] = response
                st.subheader("Результаты анализа мотивации:")
                col1, col2 = st.columns(2)
                col1.metric("Основной мотиватор", response['primary_motivation'])
                col2.metric("Вторичный мотиватор", response['secondary_motivation'])
                st.info(f"**Анализ:** {response['analysis_summary']}")
                st.success("Спасибо! Переходим к следующему этапу.")
                st.session_state.stage = 'stage_5_cognitive_test'
                st.rerun()

def render_stage_5_cognitive_test():
    st.title("Этап 5: Когнитивный тест")
    st.write("Пройдите короткий тест на логику, математику и внимательность.")

    if st.session_state.get('show_hints'):
        st.info("""
        💡 **Подсказка для демо:** Нужно ответить **минимум на 2 из 3** вопросов правильно.

        **Ответы:**
        - Логика (Зипы-Зупы): **Ложь**
        - Математика (ручка): **5 рублей**
        - Внимание (буква 'о'): **11**
        """)

    if 'questions' not in st.session_state:
        with st.spinner("Загружаем вопросы..."):
            questions = api_request("get", "/v1/screen/stage5_cognitive_test/questions")
            if questions:
                st.session_state.questions = questions
                st.rerun()
            else:
                st.error("❌ Не удалось загрузить вопросы теста. Проверьте подключение к серверу.")
                return

    with st.form("cognitive_test_form"):
        st.subheader("Вопросы теста")
        user_answers = {}
        for q in st.session_state.questions:
            user_answers[q['id']] = st.radio(q['question'], options=q['options'], key=q['id'])
        
        submitted = st.form_submit_button("Завершить тест")
        if submitted:
            answers_payload = [{"question_id": q_id, "answer": ans} for q_id, ans in user_answers.items()]
            with st.spinner("Проверяем ваши ответы..."):
                response = api_request("post", "/v1/screen/stage5_cognitive_test", json={"answers": answers_payload})
            
            if response:
                st.session_state.candidate_data['stage5_response'] = response
                st.subheader("Результат теста")
                st.metric("Ваш результат", f"{response['score']} / {response['total']}")
                
                if response['passed']:
                    st.success("Вы успешно прошли когнитивный тест!")
                    st.session_state.stage = 'stage_6_chat'
                else:
                    st.error("К сожалению, вы не прошли тест. Необходим лучший результат.")
                    st.session_state.stage = 'end_fail'
                st.rerun()

def render_stage_6_chat():
    st.title("Этап 6: Поведенческое AI-интервью")
    st.write("Вам будет задано несколько вопросов. Отвечайте честно и развернуто.")

    if st.session_state.get('show_hints'):
        st.info("""
        💡 **Подсказка для демо:** Нужно ответить на **5 вопросов**.

        Отвечайте развёрнуто (2-3 предложения), демонстрируя:
        - Проактивность и инициативу
        - Честность и самокритику
        - Структурность мышления
        - Ориентацию на результат

        Пример: *"В прошлом году я увеличил продажи на 30% благодаря новой стратегии холодных звонков. Я сам предложил эту идею и внедрил её за месяц."*
        """)
    if not st.session_state.chat_history:
        with st.spinner("Начинаем чат..."):
            response = api_request("post", "/v1/screen/stage6_behavioral_chat", json={"conversation": []})
            if response:
                st.session_state.chat_history = response['conversation']
                st.rerun()
    
    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    if st.session_state.assessment:
        st.subheader("Интервью завершено. Результаты оценки:")
        st.json(st.session_state.assessment)
        st.session_state.stage = 'end_success'
        st.button("Завершить")
        return

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
        st.json(st.session_state.candidate_data)

# --- Main App Logic ---
render_sidebar()
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
elif page == 'stage_4_motivation':
    render_stage_4_motivation()
elif page == 'stage_5_cognitive_test':
    render_stage_5_cognitive_test()
elif page == 'stage_6_chat':
    render_stage_6_chat()
elif page == 'end_success':
    render_end_page(success=True)
elif page == 'end_fail':
    render_end_page(success=False)
