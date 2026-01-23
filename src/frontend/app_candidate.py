"""
AI-HR: Интерфейс кандидата
Портал для прохождения отбора на вакансию
"""
import streamlit as st
import requests
import os
import time

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
        st.error("❌ Не удалось подключиться к серверу. Попробуйте позже.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Сервер не отвечает. Попробуйте ещё раз.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 500:
            st.error("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")
        else:
            st.error("❌ Произошла ошибка при обработке запроса.")
        return None
    except requests.exceptions.RequestException:
        st.error("❌ Ошибка соединения.")
        return None

# --- App Initialization ---
st.set_page_config(
    page_title="Отбор кандидатов | AI-HR",
    page_icon="👤",
    layout="wide"
)

if 'stage' not in st.session_state:
    st.session_state.stage = 'welcome'
if 'candidate_data' not in st.session_state:
    st.session_state.candidate_data = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'assessment' not in st.session_state:
    st.session_state.assessment = None
if 'achievements' not in st.session_state:
    st.session_state.achievements = []
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'screening_step' not in st.session_state:
    st.session_state.screening_step = 1
if 'screening_answers' not in st.session_state:
    st.session_state.screening_answers = {}
if 'unlocked_content' not in st.session_state:
    st.session_state.unlocked_content = []

# --- Unlockable Content System ---
UNLOCKABLE_CONTENT = {
    'team_insights': {
        'id': 'team_insights',
        'title': '🔓 Инсайды о команде',
        'unlock_after': 'screening',
        'content': """
### 👥 Познакомьтесь с командой!

**Типичный день менеджера по продажам:**
- 09:00 — Утренний стендап (15 мин)
- 09:30 — Блок холодных звонков
- 12:00 — Обед (компания оплачивает!)
- 13:00 — Встречи с клиентами
- 17:00 — Подведение итогов в CRM
- 18:00 — Домой (никаких переработок!)

**Цифры команды:**
- 📊 Средний стаж: 2.5 года
- 💰 Средний бонус: 45% от оклада
- 🎯 92% выполняют план
"""
    },
    'salary_benchmarks': {
        'id': 'salary_benchmarks',
        'title': '💰 Зарплатный бенчмарк',
        'unlock_after': 'motivation',
        'content': """
### 💰 Реальные зарплаты в команде

**По грейдам:**
| Грейд | Оклад | Бонус | Итого |
|-------|-------|-------|-------|
| Junior | 50-70K | 20-40K | 70-110K |
| Middle | 80-120K | 40-80K | 120-200K |
| Senior | 130-180K | 80-150K | 210-330K |

**Топ-перформеры** зарабатывают **до 400K/мес**!

🚀 *Эти данные за последний квартал*
"""
    },
    'success_stories': {
        'id': 'success_stories',
        'title': '⭐ Истории успеха',
        'unlock_after': 'interview',
        'content': """
### ⭐ Истории наших сотрудников

**Алексей, 28 лет** (был Junior → стал Team Lead за 1.5 года)
> "Пришёл без опыта в продажах. Через полгода уже был лучшим в команде.
> Секрет? Отличный онбординг и менторство."

**Мария, 32 года** (перешла из ритейла)
> "Думала, B2B — это сложно. Оказалось, здесь ценят мой опыт общения с людьми.
> Сейчас зарабатываю в 2 раза больше, чем в рознице."

**Дмитрий, 25 лет** (первая работа после универа)
> "Боялся холодных звонков. Теперь делаю 50+ в день играючи.
> Главное — скрипты и практика."
"""
    }
}

def unlock_content(content_id):
    """Unlock content for the candidate."""
    if content_id not in st.session_state.unlocked_content:
        st.session_state.unlocked_content.append(content_id)
        return UNLOCKABLE_CONTENT.get(content_id)
    return None

def check_unlocks_for_stage(stage_name):
    """Check and unlock content after completing a stage."""
    unlocked = []
    for content_id, content in UNLOCKABLE_CONTENT.items():
        if content['unlock_after'] == stage_name and content_id not in st.session_state.unlocked_content:
            unlocked.append(unlock_content(content_id))
    return [u for u in unlocked if u]

def render_unlock_notification(unlocked_content):
    """Render notification about newly unlocked content."""
    if not unlocked_content:
        return

    for content in unlocked_content:
        st.success(f"""
        🔓 **РАЗБЛОКИРОВАНО!**

        Вы открыли доступ к секретному разделу:
        **{content['title']}**
        """)

        with st.expander("👀 Посмотреть сейчас", expanded=False):
            st.markdown(content['content'])

# --- Gamification System ---
ACHIEVEMENTS = {
    'quick_start': {'name': '⚡ Быстрый старт', 'desc': 'Начали отбор менее чем за минуту', 'xp': 50},
    'screening_done': {'name': '📋 Анкета пройдена', 'desc': 'Успешно заполнили анкету', 'xp': 100},
    'resume_pro': {'name': '📄 Профи резюме', 'desc': 'Резюме оценено выше 80%', 'xp': 150},
    'resume_done': {'name': '📄 Резюме отправлено', 'desc': 'Прошли этап резюме', 'xp': 100},
    'motivation_done': {'name': '💡 Мотивация раскрыта', 'desc': 'Рассказали о своих целях', 'xp': 100},
    'cognitive_ace': {'name': '🧠 Гений логики', 'desc': 'Ответили на все вопросы правильно', 'xp': 200},
    'cognitive_done': {'name': '🧠 Тест пройден', 'desc': 'Прошли когнитивный тест', 'xp': 100},
    'interview_done': {'name': '💬 Интервью завершено', 'desc': 'Прошли AI-интервью', 'xp': 150},
    'personality_done': {'name': '🎭 Профиль раскрыт', 'desc': 'Прошли личностный тест', 'xp': 100},
    'personality_pro': {'name': '🌟 Идеальный продажник', 'desc': 'Sales Fit Score выше 75%', 'xp': 150},
    'sales_done': {'name': '💼 Сейлз-эксперт', 'desc': 'Прошли все сейлз-кейсы', 'xp': 150},
    'sales_ace': {'name': '🔥 Мастер продаж', 'desc': 'Сейлз-оценка выше 80%', 'xp': 200},
    'champion': {'name': '🏆 Чемпион', 'desc': 'Прошли весь отбор!', 'xp': 300},
}

def award_achievement(achievement_id):
    """Award an achievement to the candidate."""
    if achievement_id not in st.session_state.achievements:
        st.session_state.achievements.append(achievement_id)
        achievement = ACHIEVEMENTS.get(achievement_id)
        if achievement:
            st.session_state.xp += achievement['xp']
            return achievement
    return None

def get_candidate_stats():
    """Generate comparison stats for the candidate."""
    import random
    # В реальности это будет из БД
    return {
        'speed_percentile': random.randint(60, 95),
        'quality_percentile': random.randint(50, 90),
        'candidates_this_week': random.randint(15, 40),
    }

def render_stage_celebration(stage_name, next_stage, achievement_id=None, fun_fact=None):
    """Render celebration screen between stages."""
    # Award achievement if provided
    new_achievement = None
    if achievement_id:
        new_achievement = award_achievement(achievement_id)

    # Celebration container
    with st.container():
        st.success(f"✨ **Отлично справились!** Этап «{stage_name}» пройден!")

        # Show new achievement
        if new_achievement:
            st.markdown(f"""
            🏆 **Новое достижение!**

            **{new_achievement['name']}** — {new_achievement['desc']}

            *+{new_achievement['xp']} XP*
            """)

        # Progress indicator
        current_idx = get_stage_index(st.session_state.stage)
        total_stages = len(CANDIDATE_STAGES) - 2  # Exclude welcome and result
        progress_pct = int((current_idx / total_stages) * 100)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.progress(current_idx / total_stages)
            st.caption(f"🎯 Прогресс: {progress_pct}%")
        with col2:
            st.metric("XP", st.session_state.xp, delta=f"+{new_achievement['xp'] if new_achievement else 0}")

        # Fun fact / social proof
        if fun_fact:
            st.info(f"💡 **Интересный факт:** {fun_fact}")

        # Comparison stats
        stats = get_candidate_stats()
        st.markdown("---")
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric("Ваша скорость", f"Топ {100 - stats['speed_percentile']}%", delta="быстрее большинства")
        with stat_col2:
            st.metric("На этой неделе", f"{stats['candidates_this_week']} чел.", help="Кандидатов на эту вакансию")
        with stat_col3:
            if stats['quality_percentile'] >= 75:
                st.metric("Качество ответов", "Отлично", delta="выше среднего")
            else:
                st.metric("Качество ответов", "Хорошо")

        st.markdown("---")

        # Show pending unlocks
        pending_unlocks = st.session_state.candidate_data.get('pending_unlocks', [])
        if pending_unlocks:
            render_unlock_notification(pending_unlocks)
            # Clear pending unlocks after showing
            st.session_state.candidate_data['pending_unlocks'] = []

        # Continue button
        if st.button(f"🚀 Продолжить → {next_stage}", type="primary", use_container_width=True):
            return True

    return False

# --- Stage Progress Configuration ---
CANDIDATE_STAGES = [
    ('welcome', '👋 Приветствие'),
    ('screening', '📋 Анкета'),
    ('resume', '📄 Резюме'),
    ('motivation', '💡 Мотивация'),
    ('cognitive', '🧠 Тест'),
    ('interview', '💬 Интервью'),
    ('personality', '🎭 Личность'),
    ('sales', '💼 Сейлз-кейсы'),
    ('result', '📊 Результат'),
]

def get_stage_index(stage_key):
    for i, (key, _) in enumerate(CANDIDATE_STAGES):
        if key == stage_key:
            return i
    return 0

# --- Global Progress Bar Component ---
def render_progress_header():
    """Renders a motivational progress bar at the top of each stage."""
    current_stage = st.session_state.get('stage', 'welcome')

    # Don't show on welcome and result pages
    if current_stage in ['welcome', 'result']:
        return

    current_idx = get_stage_index(current_stage)
    total_stages = len(CANDIDATE_STAGES) - 1  # Exclude 'result' from count
    progress = current_idx / total_stages

    # Estimate remaining time based on stage
    time_estimates = {
        'screening': 18,
        'resume': 15,
        'motivation': 12,
        'cognitive': 10,
        'interview': 8,
        'personality': 5,
        'sales': 2
    }
    remaining_minutes = time_estimates.get(current_stage, 5)

    # Motivational messages
    messages = {
        'screening': "Отличное начало! Ещё немного — и мы узнаем друг друга лучше",
        'resume': "Вы на верном пути! AI уже готов проанализировать ваш опыт",
        'motivation': "Больше половины позади! Расскажите о своих целях",
        'cognitive': "Отлично идёте! Тест на логику — это легко",
        'interview': "Покажите себя в AI-интервью!",
        'personality': "Почти финиш! Узнаем ваш профиль продажника",
        'sales': "Последний рывок! Покажите свои сейлз-скиллы"
    }
    message = messages.get(current_stage, "Продолжайте в том же духе!")

    # Render progress header
    with st.container():
        cols = st.columns([3, 1])
        with cols[0]:
            st.progress(progress)
            st.caption(f"**Этап {current_idx} из {total_stages - 1}** | {message}")
        with cols[1]:
            st.markdown(f"⏱️ **~{remaining_minutes} мин**")
        st.divider()

def render_achievements_sidebar():
    """Render gamification panel in sidebar."""
    if not st.session_state.achievements:
        return

    with st.expander("🏆 Достижения", expanded=False):
        # XP Bar
        max_xp = sum(a['xp'] for a in ACHIEVEMENTS.values())
        current_xp = st.session_state.xp
        xp_progress = min(current_xp / max_xp, 1.0)

        st.markdown(f"**{current_xp} XP** из {max_xp}")
        st.progress(xp_progress)

        # Achievements list
        for ach_id in st.session_state.achievements:
            ach = ACHIEVEMENTS.get(ach_id)
            if ach:
                st.markdown(f"✅ {ach['name']}")

        # Locked achievements
        locked = [a for a_id, a in ACHIEVEMENTS.items() if a_id not in st.session_state.achievements]
        if locked:
            st.caption(f"🔒 Ещё {len(locked)} достижений")

def render_sidebar():
    with st.sidebar:
        st.title("👤 Кабинет кандидата")
        st.divider()

        current_stage = st.session_state.get('stage', 'welcome')
        current_idx = get_stage_index(current_stage)
        total_stages = len(CANDIDATE_STAGES) - 1
        progress = min(current_idx / total_stages, 1.0)

        st.subheader("📊 Прогресс отбора")
        st.progress(progress)
        st.caption(f"Этап {current_idx + 1} из {total_stages + 1}")

        # Gamification XP display
        if st.session_state.xp > 0:
            st.markdown(f"⭐ **{st.session_state.xp} XP**")

        st.divider()
        st.markdown("**Этапы:**")
        for i, (key, label) in enumerate(CANDIDATE_STAGES):
            if i < current_idx:
                st.markdown(f"✅ ~~{label}~~")
            elif i == current_idx:
                st.markdown(f"**→ {label}**")
            else:
                st.markdown(f"<span style='color: gray'>○ {label}</span>", unsafe_allow_html=True)

        # Achievements panel
        render_achievements_sidebar()

        st.divider()

        # Demo mode toggle (можно убрать в продакшене)
        if os.getenv("DEMO_MODE", "true").lower() == "true":
            st.session_state.show_hints = st.checkbox(
                "💡 Демо-подсказки",
                value=st.session_state.get('show_hints', False)
            )

        st.divider()
        if st.button("🔄 Начать заново", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.caption("AI-HR Candidate Portal v0.3")

# --- Page Rendering ---

def render_welcome():
    st.title("👋 Добро пожаловать в команду продаж!")

    # --- Блок о компании (Selling Points) ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### Менеджер по продажам B2B

        Мы ищем амбициозных специалистов, готовых расти вместе с нами!
        """)

        # Ключевые преимущества
        st.markdown("#### 💰 Что мы предлагаем:")
        benefits_col1, benefits_col2 = st.columns(2)
        with benefits_col1:
            st.markdown("""
            - 💵 **80 000 - 150 000 ₽** + бонусы
            - 📈 Рост до руководителя за 1 год
            - 🎓 Бесплатное обучение продажам
            """)
        with benefits_col2:
            st.markdown("""
            - 🏢 Гибкий график (офис/гибрид)
            - 🏖️ 28 дней отпуска
            - 🍕 Обеды за счёт компании
            """)

    with col2:
        # Статистика компании
        st.markdown("#### 🏢 О нас:")
        st.metric("Средний доход", "120 000 ₽/мес", delta="+15% к рынку")
        st.caption("87% сотрудников рекомендуют нас")

    st.divider()

    # --- Этапы как выгоды ---
    st.markdown("### 🎯 Как проходит отбор?")
    st.caption("Прозрачный процесс: вы всегда знаете, на каком этапе находитесь")

    stages_col1, stages_col2 = st.columns(2)

    with stages_col1:
        st.markdown("""
        **1. Быстрая анкета** (2 мин)
        → Узнаете, подходит ли вам вакансия

        **2. AI-анализ резюме** (3 мин)
        → Получите обратную связь о ваших сильных сторонах

        **3. Мотивация** (3 мин)
        → Поможем подобрать команду под ваш стиль
        """)

    with stages_col2:
        st.markdown("""
        **4. Мини-тест на логику** (5 мин)
        → Без стресса, всего 3 вопроса

        **5. AI-интервью** (10 мин)
        → Разговор, не допрос. В удобное вам время

        **6. Результат**
        → Мгновенный ответ, без ожидания
        """)

    st.divider()

    # --- Прогресс и Social Proof ---
    progress_col, social_col = st.columns([1, 1])

    with progress_col:
        st.markdown("#### ⏱️ Время прохождения")
        st.progress(0.8)
        st.caption("**80% кандидатов** завершают отбор за **15 минут**")

    with social_col:
        st.markdown("#### 💬 Отзыв кандидата")
        st.info("""
        *"Прошёл отбор за 12 минут и через неделю уже вышел на работу! Очень удобный формат."*
        — Алексей С., менеджер по продажам
        """)

    st.divider()

    # --- CTA ---
    cta_col1, cta_col2 = st.columns([2, 1])

    with cta_col1:
        if st.button("🚀 Начать отбор", type="primary", use_container_width=True):
            st.session_state.stage = 'screening'
            st.session_state.start_time = time.time()
            # Quick start achievement (if clicked within 60 seconds of page load)
            award_achievement('quick_start')
            st.rerun()

    with cta_col2:
        st.caption("💾 Прогресс сохраняется автоматически")

    # Дополнительная информация
    with st.expander("💡 Советы для успешного прохождения"):
        st.markdown("""
        - 📄 **Подготовьте резюме** — текст или файл
        - ⏰ **Выделите 15-20 минут** без отвлечений
        - 💬 **Отвечайте честно** — нет "правильных" ответов
        - 🎯 **Будьте конкретны** — примеры из опыта ценятся
        """)

def render_screening():
    render_progress_header()
    st.title("📋 Этап 1: Анкета")

    # Mini progress for wizard steps
    step = st.session_state.screening_step
    total_steps = 3

    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #4CAF50 {step/total_steps*100}%, #e0e0e0 {step/total_steps*100}%);
                height: 8px; border-radius: 4px; margin-bottom: 20px;"></div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (col, label) in enumerate(zip(cols, ["📞 Звонки", "🏢 Формат", "💰 Зарплата"]), 1):
        with col:
            if i < step:
                st.markdown(f"<div style='text-align:center;color:#4CAF50'>✅ {label}</div>", unsafe_allow_html=True)
            elif i == step:
                st.markdown(f"<div style='text-align:center;font-weight:bold'>👉 {label}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center;color:#999'>{label}</div>", unsafe_allow_html=True)

    st.divider()

    if st.session_state.get('show_hints'):
        st.info("""
        💡 **Демо:** Чтобы пройти этап:
        - Холодные звонки: **ДА**
        - Формат: **office**
        - Зарплата: **≤ 60 000**
        """)

    # === STEP 1: Cold Calls ===
    if step == 1:
        st.subheader("📞 Шаг 1: Готовность к холодным звонкам")

        st.markdown("""
        **Почему мы спрашиваем?**

        Холодные звонки — ключевая часть работы менеджера по продажам.
        Мы хотим убедиться, что вы готовы к этому с первого дня.

        🎯 *85% наших топ-перформеров начинали именно с холодных звонков*
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Да, готов(а)!", type="primary", use_container_width=True):
                st.session_state.screening_answers['cold_calls'] = True
                st.session_state.screening_step = 2
                st.rerun()
        with col2:
            if st.button("❌ Нет, не готов(а)", use_container_width=True):
                st.session_state.screening_answers['cold_calls'] = False
                # Сразу показываем отказ
                st.error("❌ К сожалению, для данной вакансии обязательна готовность к холодным звонкам.")
                st.warning("Но не расстраивайтесь! Возможно, вам подойдут другие позиции.")
                st.session_state.candidate_data['screening'] = {
                    'passed': False,
                    'answers': [{"question_id": "cold_calls", "answer": False}],
                    'rejection_reasons': ["Не готов к холодным звонкам"]
                }
                st.session_state.candidate_data['final_status'] = 'rejected'
                st.session_state.candidate_data['rejection_stage'] = 'screening'
                time.sleep(2)
                st.session_state.stage = 'result'
                st.rerun()

    # === STEP 2: Work Format ===
    elif step == 2:
        st.subheader("🏢 Шаг 2: Формат работы")

        st.markdown("""
        **Какой формат вам ближе?**

        Мы ценим комфорт наших сотрудников и предлагаем разные варианты.
        """)

        format_options = [
            ("office", "🏢 Офис", "Работа в команде, быстрый рост, менторство"),
            ("hybrid", "🔄 Гибрид", "2-3 дня в офисе, остальное — из дома"),
            ("remote", "🏠 Удалённо", "Полная свобода локации"),
        ]

        for fmt_id, fmt_name, fmt_desc in format_options:
            if st.button(f"{fmt_name}\n\n_{fmt_desc}_", key=f"fmt_{fmt_id}", use_container_width=True):
                st.session_state.screening_answers['work_format'] = fmt_id
                st.session_state.screening_step = 3
                st.rerun()

        st.divider()
        if st.button("← Назад", key="back_to_1"):
            st.session_state.screening_step = 1
            st.rerun()

    # === STEP 3: Salary ===
    elif step == 3:
        st.subheader("💰 Шаг 3: Зарплатные ожидания")

        st.markdown("""
        **Сколько вы хотите зарабатывать?**

        Будьте честны — это поможет понять, подходит ли вакансия.

        📊 *Средняя зарплата в команде: 80-150K ₽/мес (оклад + бонусы)*
        """)

        salary = st.slider(
            "Ваши ожидания (₽/мес)",
            min_value=30000,
            max_value=300000,
            value=st.session_state.screening_answers.get('salary_expectation', 80000),
            step=5000,
            format="%d ₽"
        )

        # Visual feedback
        if salary <= 100000:
            st.success("✅ Отлично! Это в пределах бюджета для Junior/Middle позиций")
        elif salary <= 180000:
            st.info("👍 Хорошо! Это соответствует Middle/Senior позициям")
        else:
            st.warning("⚠️ Высокие ожидания. Возможно, потребуется обсуждение с руководителем")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Назад", key="back_to_2", use_container_width=True):
                st.session_state.screening_step = 2
                st.rerun()
        with col2:
            if st.button("Завершить анкету ✓", type="primary", use_container_width=True):
                st.session_state.screening_answers['salary_expectation'] = salary
                # Submit all answers
                answers = [
                    {"question_id": "cold_calls", "answer": st.session_state.screening_answers.get('cold_calls', False)},
                    {"question_id": "work_format", "answer": st.session_state.screening_answers.get('work_format', 'office')},
                    {"question_id": "salary_expectation", "answer": salary}
                ]

                with st.spinner("Проверяем ваши ответы..."):
                    response = api_request("post", "/v1/screen/stage2_screening", json={"answers": answers})

                if response:
                    st.session_state.candidate_data['screening'] = {
                        'passed': response['passed'],
                        'answers': answers
                    }
                    if response['passed']:
                        award_achievement('screening_done')
                        # Check for unlocks
                        unlocked = check_unlocks_for_stage('screening')
                        if unlocked:
                            st.session_state.candidate_data['pending_unlocks'] = unlocked
                        st.session_state.candidate_data['show_celebration'] = 'screening'
                        st.session_state.stage = 'resume'
                        # Reset wizard for next time
                        st.session_state.screening_step = 1
                        st.session_state.screening_answers = {}
                    else:
                        st.error("К сожалению, ваш профиль не соответствует требованиям вакансии.")
                        st.session_state.candidate_data['final_status'] = 'rejected'
                        st.session_state.candidate_data['rejection_stage'] = 'screening'
                        st.session_state.stage = 'result'
                    st.rerun()

def render_resume():
    # Check for celebration from previous stage
    if st.session_state.candidate_data.get('show_celebration') == 'screening':
        if render_stage_celebration(
            stage_name="Анкета",
            next_stage="Анализ резюме",
            achievement_id=None,  # Already awarded
            fun_fact="92% кандидатов, прошедших анкету, получают оффер!"
        ):
            del st.session_state.candidate_data['show_celebration']
            st.rerun()
        return

    render_progress_header()
    st.title("📄 Этап 2: Анализ резюме")

    # Value proposition для AI-анализа
    st.markdown("""
    🤖 **Наш AI проанализирует:**
    - ✓ Соответствие вакансии (0-100%)
    - ✓ Ваши сильные стороны
    - ✓ Рекомендации по улучшению

    ⚡ *Анализ займёт всего 5 секунд!*
    """)

    if st.session_state.get('show_hints'):
        st.info("""
        💡 **Демо:** Нужно **≥65 баллов**.
        Пример резюме: *"Иван Петров. Опыт в B2B продажах 5 лет. CRM Bitrix24. План 120%."*
        """)

    # Показываем требования вакансии (в реальности будут загружаться из БД)
    with st.expander("📋 Требования вакансии"):
        st.markdown("""
        - Опыт работы в продажах от 2 лет
        - Знание CRM-систем
        - Навыки переговоров и презентаций
        - Готовность к холодным звонкам
        """)

    with st.form("resume_form"):
        resume_text = st.text_area(
            "Вставьте текст вашего резюме",
            height=300,
            placeholder="Например:\nИван Иванов\nОпыт работы: 5 лет в B2B продажах\nДостижения: выполнение плана на 120%..."
        )

        submitted = st.form_submit_button("Отправить резюме", type="primary", use_container_width=True)

        if submitted:
            if len(resume_text.strip()) < 50:
                st.error("Пожалуйста, введите более подробное резюме (минимум 50 символов)")
            else:
                # В реальности job_description будет загружаться из БД
                job_description = "Менеджер по продажам B2B. Требования: опыт от 2 лет, знание CRM, навыки переговоров."

                with st.spinner("AI анализирует ваше резюме..."):
                    response = api_request("post", "/v1/screen/stage3_resume_scoring", json={
                        "job_description": job_description,
                        "resume_text": resume_text
                    })

                if response:
                    passed = response['score'] >= 65
                    score = response['score']

                    # Сохраняем данные
                    st.session_state.candidate_data['resume'] = {
                        'passed': passed,
                        'score': score,
                        'summary': response.get('summary', '')
                    }

                    if passed:
                        # Award achievements
                        award_achievement('resume_done')
                        if score >= 80:
                            award_achievement('resume_pro')

                        # Персонализированный позитивный фидбек
                        st.success("✨ **Отличные результаты!**")

                        # Показываем результат анализа
                        result_col1, result_col2 = st.columns([1, 2])
                        with result_col1:
                            st.metric("Соответствие", f"{score}%", delta=f"+{score-65}% от минимума")
                        with result_col2:
                            st.markdown("""
                            **💪 Ваши сильные стороны:**
                            - Релевантный опыт работы
                            - Соответствие ключевым требованиям
                            """)

                        # Совет (если есть что улучшить)
                        if score < 85:
                            st.info("💡 **Совет:** Добавьте конкретные цифры достижений для усиления резюме в будущем!")

                        st.markdown("---")
                        st.markdown("⏭️ **Готовы к следующему этапу?**")

                        # Mark celebration and move to next stage
                        st.session_state.candidate_data['show_celebration'] = 'resume'
                        time.sleep(1.5)
                        st.session_state.stage = 'motivation'
                    else:
                        st.error("К сожалению, ваш опыт недостаточно соответствует требованиям вакансии.")
                        st.session_state.candidate_data['final_status'] = 'rejected'
                        st.session_state.candidate_data['rejection_stage'] = 'resume'
                        st.session_state.stage = 'result'
                    st.rerun()

def render_motivation():
    # Check for celebration from previous stage
    if st.session_state.candidate_data.get('show_celebration') == 'resume':
        resume_score = st.session_state.candidate_data.get('resume', {}).get('score', 0)
        if render_stage_celebration(
            stage_name="Анализ резюме",
            next_stage="Мотивация",
            achievement_id=None,
            fun_fact=f"Ваш результат {resume_score}% — это отличный показатель!"
        ):
            del st.session_state.candidate_data['show_celebration']
            st.rerun()
        return

    render_progress_header()
    st.title("💡 Этап 3: Мотивация")

    # Объяснение зачем это нужно
    st.info("""
    🎯 **Зачем мы спрашиваем?**
    Ваши ответы помогут нам подобрать:
    - Подходящую команду
    - Правильного наставника
    - Проекты по интересам
    """)

    if st.session_state.get('show_hints'):
        st.info("💡 **Демо:** Этот этап не отсеивает — просто классифицирует мотивацию.")

    with st.form("motivation_form"):
        answer_motivation = st.text_area(
            "Что вас мотивирует в работе больше всего?",
            placeholder="Например: возможность влиять на продукт, высокий доход, карьерный рост...",
            height=100
        )

        answer_reason_for_leaving = st.text_area(
            "Почему вы решили сменить работу?",
            placeholder="Например: ищу новые вызовы, хочу развиваться в другой области...",
            height=100
        )

        answer_kpi = st.text_area(
            "Как вы относитесь к работе по KPI и планам продаж?",
            placeholder="Например: положительно, это помогает фокусироваться на результате...",
            height=100
        )

        submitted = st.form_submit_button("Отправить ответы", type="primary", use_container_width=True)

        if submitted:
            if not all([answer_motivation.strip(), answer_reason_for_leaving.strip(), answer_kpi.strip()]):
                st.error("Пожалуйста, ответьте на все вопросы")
            else:
                with st.spinner("AI анализирует ваши ответы..."):
                    response = api_request("post", "/v1/screen/stage4_motivation_survey", json={
                        "answer_motivation": answer_motivation,
                        "answer_reason_for_leaving": answer_reason_for_leaving,
                        "answer_kpi": answer_kpi
                    })

                if response:
                    # Кандидат не видит детальный анализ мотивации
                    st.session_state.candidate_data['motivation'] = response
                    award_achievement('motivation_done')
                    # Check for unlocks
                    unlocked = check_unlocks_for_stage('motivation')
                    if unlocked:
                        st.session_state.candidate_data['pending_unlocks'] = unlocked
                    st.session_state.candidate_data['show_celebration'] = 'motivation'
                    st.session_state.stage = 'cognitive'
                    st.rerun()

def render_cognitive():
    # Check for celebration from previous stage
    if st.session_state.candidate_data.get('show_celebration') == 'motivation':
        if render_stage_celebration(
            stage_name="Мотивация",
            next_stage="Мини-тест",
            achievement_id=None,
            fun_fact="Вы уже прошли больше половины отбора! До финиша совсем близко."
        ):
            del st.session_state.candidate_data['show_celebration']
            st.rerun()
        return

    render_progress_header()
    st.title("🧠 Этап 4: Мини-тест на логику")

    # Снятие стресса перед тестом
    st.success("""
    😊 **Не переживайте!** Это не экзамен.

    - 📊 Всего **3 быстрых вопроса**
    - ⏱️ **Без ограничения времени** — думайте спокойно
    - 💡 Большинство справляются за **2-3 минуты**
    """)

    if st.session_state.get('show_hints'):
        st.info("""
        💡 **Демо:** Минимум **2 из 3** правильных.
        Ответы: Логика — **Ложь**, Математика — **5 рублей**, Внимание — **11**
        """)

    if 'questions' not in st.session_state:
        with st.spinner("Загружаем тест..."):
            questions = api_request("get", "/v1/screen/stage5_cognitive_test/questions")
            if questions:
                st.session_state.questions = questions
                st.rerun()
            else:
                st.error("❌ Не удалось загрузить тест.")
                return

    with st.form("cognitive_form"):
        st.markdown("**Ответьте на следующие вопросы:**")
        user_answers = {}

        for i, q in enumerate(st.session_state.questions, 1):
            st.markdown(f"**Вопрос {i}:**")
            user_answers[q['id']] = st.radio(
                q['question'],
                options=q['options'],
                key=q['id'],
                label_visibility="visible"
            )
            st.divider()

        submitted = st.form_submit_button("Завершить тест", type="primary", use_container_width=True)

        if submitted:
            answers_payload = [{"question_id": q_id, "answer": ans} for q_id, ans in user_answers.items()]
            with st.spinner("Проверяем ответы..."):
                response = api_request("post", "/v1/screen/stage5_cognitive_test", json={"answers": answers_payload})

            if response:
                st.session_state.candidate_data['cognitive'] = response

                # Кандидат видит свой результат
                st.metric("Ваш результат", f"{response['score']} из {response['total']}")

                if response['passed']:
                    award_achievement('cognitive_done')
                    if response['score'] == response['total']:
                        award_achievement('cognitive_ace')
                    st.session_state.candidate_data['show_celebration'] = 'cognitive'
                    st.session_state.stage = 'interview'
                else:
                    st.error("К сожалению, результат теста недостаточен для продолжения.")
                    st.session_state.candidate_data['final_status'] = 'rejected'
                    st.session_state.candidate_data['rejection_stage'] = 'cognitive'
                    st.session_state.stage = 'result'
                st.rerun()

def render_interview():
    # Check for celebration from previous stage
    if st.session_state.candidate_data.get('show_celebration') == 'cognitive':
        cognitive = st.session_state.candidate_data.get('cognitive', {})
        score = cognitive.get('score', 0)
        total = cognitive.get('total', 3)
        if render_stage_celebration(
            stage_name="Когнитивный тест",
            next_stage="AI-Интервью",
            achievement_id=None,
            fun_fact=f"Результат {score}/{total} — отличная работа! Финальный этап совсем рядом."
        ):
            del st.session_state.candidate_data['show_celebration']
            st.rerun()
        return

    render_progress_header()
    st.title("💬 Этап 5: AI-Интервью")

    # Снятие стресса перед интервью
    if not st.session_state.chat_history:
        st.success("""
        🎉 **Финальный этап!** Расслабьтесь, это разговор, а не допрос.

        **Что вас ждёт:**
        - 4-5 простых вопросов о вашем опыте
        - Отвечайте в свободной форме
        - Нет правильных или неправильных ответов

        💡 *Совет: Будьте собой и говорите искренне*
        """)

    if st.session_state.get('show_hints'):
        st.info("💡 **Демо:** Нужно ответить на **5 вопросов**. Пишите развёрнуто (2-3 предложения).")

    if not st.session_state.chat_history:
        with st.spinner("Начинаем интервью..."):
            response = api_request("post", "/v1/screen/stage6_behavioral_chat", json={"conversation": []})
            if response:
                st.session_state.chat_history = response['conversation']
                st.rerun()

    # Показываем историю чата
    for message in st.session_state.chat_history:
        role = "assistant" if message['role'] == "assistant" else "user"
        with st.chat_message(role):
            st.markdown(message['content'])

    # Проверяем, завершено ли интервью
    if st.session_state.assessment:
        # Сохраняем данные СРАЗУ, до любых кнопок
        if 'interview' not in st.session_state.candidate_data:
            st.session_state.candidate_data['interview'] = st.session_state.assessment
            award_achievement('interview_done')
            # Check for unlocks
            unlocked = check_unlocks_for_stage('interview')
            if unlocked:
                st.session_state.candidate_data['pending_unlocks'] = unlocked

        st.balloons()
        st.success("🎉 **AI-интервью завершено!**")

        # Переход к личностному профилю
        st.session_state.candidate_data['show_celebration'] = 'interview'
        st.session_state.stage = 'personality'
        time.sleep(1)
        st.rerun()
        return

    # Поле для ввода ответа
    if prompt := st.chat_input("Введите ваш ответ..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.spinner("AI обрабатывает ваш ответ..."):
            response = api_request("post", "/v1/screen/stage6_behavioral_chat", json={
                "conversation": st.session_state.chat_history
            })
            if response:
                st.session_state.chat_history = response['conversation']
                if response.get('assessment'):
                    st.session_state.assessment = response['assessment']
                st.rerun()

def render_personality():
    # Check for celebration from previous stage
    if st.session_state.candidate_data.get('show_celebration') == 'interview':
        if render_stage_celebration(
            stage_name="AI-Интервью",
            next_stage="Личностный профиль",
            achievement_id=None,
            fun_fact="Вы прошли самый сложный этап! Осталось совсем немного."
        ):
            del st.session_state.candidate_data['show_celebration']
            st.rerun()
        return

    render_progress_header()
    st.title("🎭 Этап 6: Личностный профиль")

    st.info("""
    🎯 **Зачем этот тест?**
    Мы хотим понять ваш стиль работы, чтобы:
    - Подобрать идеальную команду
    - Определить подходящие проекты
    - Создать комфортные условия для вашего успеха

    ⚡ *Нет правильных или неправильных ответов — отвечайте честно!*
    """)

    if st.session_state.get('show_hints'):
        st.info("💡 **Демо:** Выбирайте ответы с высокими баллами (5) для лучшего результата.")

    # Загружаем вопросы
    if 'personality_questions' not in st.session_state:
        with st.spinner("Загружаем тест..."):
            questions = api_request("get", "/v1/screen/stage7_personality/questions")
            if questions:
                st.session_state.personality_questions = questions
                st.rerun()
            else:
                st.error("❌ Не удалось загрузить тест.")
                return

    questions = st.session_state.personality_questions

    with st.form("personality_form"):
        st.markdown("**Выберите вариант, который лучше всего описывает вас:**")

        answers = []
        for i, q in enumerate(questions, 1):
            st.markdown(f"**{i}. {q['text']}**")

            # Создаём опции как радио-кнопки
            options = q['options']
            option_texts = [opt['text'] for opt in options]

            selected = st.radio(
                f"Вопрос {i}",
                options=option_texts,
                key=f"pers_{q['id']}",
                label_visibility="collapsed"
            )

            # Находим выбранное значение
            selected_value = next((opt['value'] for opt in options if opt['text'] == selected), 3)
            answers.append({"question_id": q['id'], "value": selected_value})

            if i < len(questions):
                st.divider()

        submitted = st.form_submit_button("Завершить тест", type="primary", use_container_width=True)

        if submitted:
            with st.spinner("AI анализирует ваш профиль..."):
                response = api_request("post", "/v1/screen/stage7_personality", json={"answers": answers})

            if response:
                st.session_state.candidate_data['personality'] = response

                # Показываем результат
                sales_fit = response.get('sales_fit_score', 50)
                st.metric("Sales Fit Score", f"{sales_fit}/100")

                # Award achievements
                award_achievement('personality_done')
                if sales_fit >= 75:
                    award_achievement('personality_pro')

                # Проверяем красные флаги
                red_flags = response.get('red_flags', [])
                if len(red_flags) >= 2 and sales_fit < 40:
                    st.error("К сожалению, по результатам теста мы не можем продолжить процесс.")
                    st.session_state.candidate_data['final_status'] = 'rejected'
                    st.session_state.candidate_data['rejection_stage'] = 'personality'
                    st.session_state.stage = 'result'
                else:
                    st.success(f"✨ **Отличный профиль!** Sales Fit: {sales_fit}%")
                    st.session_state.candidate_data['show_celebration'] = 'personality'
                    st.session_state.stage = 'sales'

                time.sleep(1)
                st.rerun()


def render_sales():
    # Check for celebration from previous stage
    if st.session_state.candidate_data.get('show_celebration') == 'personality':
        personality = st.session_state.candidate_data.get('personality', {})
        sales_fit = personality.get('sales_fit_score', 0)
        if render_stage_celebration(
            stage_name="Личностный профиль",
            next_stage="Сейлз-кейсы",
            achievement_id=None,
            fun_fact=f"Ваш Sales Fit Score {sales_fit}% — это отличный показатель для продажника!"
        ):
            del st.session_state.candidate_data['show_celebration']
            st.rerun()
        return

    render_progress_header()
    st.title("💼 Этап 7: Сейлз-кейсы")

    st.success("""
    🎯 **Финальный рывок!** Покажите свои навыки продаж.

    **Что вас ждёт:**
    - 5-6 ситуационных вопросов
    - Реальные кейсы из практики продаж
    - AI оценит ваши ответы

    💡 *Совет: Отвечайте конкретно, приводите примеры из опыта*
    """)

    if st.session_state.get('show_hints'):
        st.info("💡 **Демо:** Пишите развёрнутые ответы (2-3 предложения). Используйте конкретные техники продаж.")

    # Загружаем сценарии
    if 'sales_scenarios' not in st.session_state:
        with st.spinner("Загружаем кейсы..."):
            scenarios = api_request("get", "/v1/screen/stage8_sales/scenarios")
            if scenarios:
                st.session_state.sales_scenarios = scenarios
                st.rerun()
            else:
                st.error("❌ Не удалось загрузить кейсы.")
                return

    scenarios = st.session_state.sales_scenarios

    with st.form("sales_form"):
        st.markdown("**Ответьте на ситуационные вопросы:**")

        answers = []
        for i, scenario in enumerate(scenarios, 1):
            type_labels = {
                'situation': '🎯 Ситуация',
                'motivation': '💡 Мотивация',
                'experience': '📈 Опыт',
                'objection': '🛡️ Возражение',
                'cold_calling': '📞 Холодный звонок'
            }
            type_label = type_labels.get(scenario['type'], '❓ Вопрос')

            st.markdown(f"**{i}. {type_label}**")
            st.markdown(f"*{scenario['text']}*")

            answer = st.text_area(
                f"Ваш ответ на вопрос {i}",
                key=f"sales_{scenario['id']}",
                height=100,
                placeholder="Опишите ваши действия или ответ...",
                label_visibility="collapsed"
            )
            answers.append({"scenario_id": scenario['id'], "answer": answer})

            if i < len(scenarios):
                st.divider()

        submitted = st.form_submit_button("Завершить отбор", type="primary", use_container_width=True)

        if submitted:
            # Проверяем, что все ответы заполнены
            empty_answers = [a for a in answers if len(a['answer'].strip()) < 10]
            if empty_answers:
                st.error(f"Пожалуйста, ответьте на все вопросы (минимум 10 символов). Пустых ответов: {len(empty_answers)}")
            else:
                with st.spinner("AI оценивает ваши ответы..."):
                    response = api_request("post", "/v1/screen/stage8_sales", json={"answers": answers})

                if response:
                    st.session_state.candidate_data['sales'] = response

                    # Показываем результат
                    overall_score = response.get('overall_sales_score', 50)
                    st.metric("Общая сейлз-оценка", f"{overall_score}/100")

                    # Award achievements
                    award_achievement('sales_done')
                    if overall_score >= 80:
                        award_achievement('sales_ace')

                    # Финальная оценка
                    concerns = response.get('concerns', [])
                    if overall_score < 40 and len(concerns) >= 3:
                        st.error("К сожалению, по результатам оценки мы не можем продолжить процесс.")
                        st.session_state.candidate_data['final_status'] = 'rejected'
                        st.session_state.candidate_data['rejection_stage'] = 'sales'
                    else:
                        st.balloons()
                        st.success(f"🎉 **Поздравляем!** Вы прошли весь отбор!")
                        award_achievement('champion')
                        st.session_state.candidate_data['final_status'] = 'completed'

                    st.session_state.stage = 'result'
                    time.sleep(1.5)
                    st.rerun()


def render_result():
    st.title("📊 Результаты отбора")

    status = st.session_state.candidate_data.get('final_status', 'unknown')

    if status == 'completed':
        # === УСПЕХ ===
        st.balloons()
        st.success("🎉 **ПОЗДРАВЛЯЕМ!** Вы успешно прошли все этапы отбора!")

        # Результаты
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Этапов пройдено", "5 из 5", delta="100%")
        with col2:
            cognitive = st.session_state.candidate_data.get('cognitive', {})
            if cognitive:
                st.metric("Тест на логику", f"{cognitive.get('score', 0)}/{cognitive.get('total', 3)}")
        with col3:
            resume = st.session_state.candidate_data.get('resume', {})
            if resume:
                st.metric("Резюме", f"{resume.get('score', 85)}%")

        st.markdown("---")

        # Что дальше
        st.markdown("### 📞 Что дальше?")

        next_col1, next_col2 = st.columns(2)
        with next_col1:
            st.markdown("""
            **1️⃣ В течение 24 часов** с вами свяжется HR-менеджер

            **2️⃣ Вы получите:**
            - Детали вакансии и условия
            - Приглашение на встречу с командой
            - Ответы на все вопросы
            """)
        with next_col2:
            st.info("""
            **💌 Подготовьтесь:**
            - ✓ Сформулируйте вопросы о вакансии
            - ✓ Подумайте о зарплатных ожиданиях
            - ✓ Подготовьте рекомендации (если есть)
            """)

        st.success("🏆 **Вы в числе лучших кандидатов!** Ждите звонка.")

        # Show all achievements
        if st.session_state.achievements:
            st.markdown("---")
            st.markdown("### 🏆 Ваши достижения")
            ach_cols = st.columns(min(len(st.session_state.achievements), 4))
            for i, ach_id in enumerate(st.session_state.achievements):
                ach = ACHIEVEMENTS.get(ach_id)
                if ach:
                    with ach_cols[i % 4]:
                        st.markdown(f"""
                        **{ach['name']}**

                        {ach['desc']}

                        *+{ach['xp']} XP*
                        """)
            st.metric("Всего XP", st.session_state.xp)

    elif status == 'rejected':
        # === ОТКАЗ ===
        rejection_stage = st.session_state.candidate_data.get('rejection_stage', 'unknown')

        # Мягкое сообщение
        st.warning("🤝 **Спасибо за участие в отборе!**")

        stage_messages = {
            'screening': "К сожалению, по результатам анкеты ваш профиль не соответствует текущим требованиям вакансии.",
            'resume': "К сожалению, по результатам анализа резюме мы не можем продолжить процесс на эту позицию.",
            'cognitive': "К сожалению, по результатам когнитивного теста мы не можем продолжить процесс."
        }
        st.markdown(stage_messages.get(rejection_stage, "К сожалению, мы не можем продолжить процесс."))

        st.markdown("---")

        # Детальный анализ — что получилось хорошо
        st.markdown("### 📈 Ваш детальный анализ")

        analysis_col1, analysis_col2 = st.columns(2)

        with analysis_col1:
            st.markdown("**✅ Что получилось отлично:**")
            # Динамически показываем пройденные этапы
            screening = st.session_state.candidate_data.get('screening', {})
            resume = st.session_state.candidate_data.get('resume', {})
            cognitive = st.session_state.candidate_data.get('cognitive', {})

            if rejection_stage != 'screening':
                if screening.get('passed'):
                    st.markdown("- ✓ Анкета: соответствие критериям")
            if rejection_stage not in ['screening', 'resume']:
                if resume.get('passed'):
                    st.markdown(f"- ✓ Резюме: {resume.get('score', 'N/A')}% соответствия")

        with analysis_col2:
            st.markdown("**⚠️ Где можно улучшиться:**")
            if rejection_stage == 'screening':
                st.markdown("""
                - Готовность к холодным звонкам
                - Соответствие зарплатных ожиданий
                """)
            elif rejection_stage == 'resume':
                st.markdown("""
                - Опыт в целевой отрасли
                - Конкретные достижения с цифрами
                """)
            elif rejection_stage == 'cognitive':
                score = cognitive.get('score', 0)
                total = cognitive.get('total', 3)
                st.markdown(f"""
                - Когнитивный тест: {score}/{total}
                - Логические задачи
                """)

        st.markdown("---")

        # Ресурсы и мотивация
        st.markdown("### 🌟 Не расстраивайтесь!")
        st.markdown("Каждый отбор — это опыт. Вот что мы рекомендуем:")

        resources_col1, resources_col2 = st.columns(2)

        with resources_col1:
            st.markdown("""
            **📚 Бесплатные ресурсы:**
            - 🧠 Тренажёр логических задач
            - 📝 Шаблоны продающего резюме
            - 🎯 Гайд по прохождению интервью
            """)

        with resources_col2:
            st.markdown("""
            **🔄 Попробуйте снова:**
            Вы сможете пройти отбор заново через 30 дней.

            *Используйте это время для подготовки!*
            """)

        st.markdown("---")

        # Альтернативные вакансии
        st.markdown("### 💼 Другие возможности")
        st.info("""
        У нас есть похожие вакансии, которые могут вам подойти:

        **1. Junior Sales Manager** — 50 000-70 000 ₽ (без требований к тесту)

        **2. Sales Development Representative** — 60 000-80 000 ₽ (удалёнка)

        *Свяжитесь с нами: hr@company.ru*
        """)

        st.markdown("**Спасибо за ваше время! Мы верим в ваш потенциал 💪**")

    else:
        st.warning("Статус отбора неизвестен.")

    st.divider()
    if st.button("🔄 Начать новый отбор", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- Main App Logic ---
render_sidebar()

page = st.session_state.get('stage', 'welcome')

if page == 'welcome':
    render_welcome()
elif page == 'screening':
    render_screening()
elif page == 'resume':
    render_resume()
elif page == 'motivation':
    render_motivation()
elif page == 'cognitive':
    render_cognitive()
elif page == 'interview':
    render_interview()
elif page == 'personality':
    render_personality()
elif page == 'sales':
    render_sales()
elif page == 'result':
    render_result()
