"""
Database configuration and session management
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://aihr:aihr_secret@localhost:5433/aihr_db")

# Railway provides postgresql:// but we need postgresql+asyncpg:// for async
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Disable SQL echo in production for security
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SQL_ECHO = ENVIRONMENT != "production"

engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    """Dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Default prompts to seed (hardcoded fallbacks)
DEFAULT_PROMPTS = {
    "job_generation": {
        "name": "Job Posting Generation",
        "description": "Generates job posting from HR brief",
        "system_message": "Ты HR-эксперт. Отвечай только валидным JSON.",
        "prompt_template": """Ты — опытный HR-специалист по подбору менеджеров по продажам. Сгенерируй привлекательную вакансию на основе брифа.

**Бриф:**
- Должность: {job_title}
- Компания: {company_name}
- Описание компании: {company_description}
- Сегмент продаж: {sales_segment}
- Зарплата: {salary_range}
- План продаж: {sales_target}
- Формат работы: {work_format}
- Дополнительные требования: {additional_requirements}

**Верни JSON-объект со следующей структурой:**
{{
  "job_title_final": "Привлекательное название вакансии",
  "job_description": "Полное описание вакансии (3-4 абзаца)",
  "requirements": ["Требование 1", "Требование 2", ...],
  "nice_to_have": ["Желательно 1", "Желательно 2", ...],
  "benefits": ["Бенефит 1", "Бенефит 2", ...],
  "screening_questions": [
    {{"question": "Вопрос 1", "type": "yes_no"}},
    {{"question": "Вопрос 2", "type": "text"}}
  ],
  "salary_display": "Красиво отформатированная зарплата",
  "tags": ["тег1", "тег2", ...]
}}""",
        "template_variables": ["job_title", "company_name", "company_description", "sales_segment", "salary_range", "sales_target", "work_format", "additional_requirements"],
        "temperature": 0.7
    },
    "resume_scoring": {
        "name": "Resume Scoring",
        "description": "AI analysis of resume against job description",
        "system_message": None,
        "prompt_template": """You are an expert HR manager. Analyze a resume against a job description. Return a JSON object with 'score' (0-100), 'summary' (2-3 sentences), and 'red_flags' (a list of strings).

**Job Description:**
{job_description}

**Candidate's Resume:**
{resume_text}""",
        "template_variables": ["job_description", "resume_text"],
        "temperature": 0.3
    },
    "motivation_survey": {
        "name": "Motivation Survey",
        "description": "Classifies candidate career motivations",
        "system_message": "You are an HR psychologist. Respond only with valid JSON.",
        "prompt_template": """You are an HR psychologist. Analyze the following answers from a candidate to determine their primary and secondary career motivations.

**Candidate's Answers:**
1. Q: Что вас мотивирует в работе больше всего?
   A: {answer_motivation}
2. Q: Почему вы решили сменить работу?
   A: {answer_reason_for_leaving}
3. Q: Как вы относитесь к работе по KPI?
   A: {answer_kpi}

- **Primary Motivations:** 'Деньги', 'Карьера', 'Стабильность', 'Интерес к задачам'
- **Secondary Motivations:** 'Признание', 'Коллектив', 'Обучение', 'Баланс работы и жизни'

Return JSON: {{"primary_motivation": "...", "secondary_motivation": "...", "summary": "..."}}""",
        "template_variables": ["answer_motivation", "answer_reason_for_leaving", "answer_kpi"],
        "temperature": 0.5
    },
    "behavioral_assessment": {
        "name": "Behavioral Interview Assessment",
        "description": "Evaluates candidate based on behavioral interview",
        "system_message": None,
        "prompt_template": """Ты — опытный HR-директор. Проанализируй диалог с кандидатом и верни JSON-объект с оценками по 5 компетенциям (proactivity, honesty, resilience, structure, motivation) от 1 до 10 и итоговым резюме 'final_summary'.

**Диалог:**
{chat_history}

Return JSON: {{"proactivity": N, "honesty": N, "resilience": N, "structure": N, "motivation": N, "final_summary": "..."}}""",
        "template_variables": ["chat_history"],
        "temperature": 0.5
    },
    "sales_evaluation": {
        "name": "Sales Evaluation",
        "description": "Evaluates sales competencies from scenario responses",
        "system_message": None,
        "prompt_template": """Ты опытный HR-специалист по найму менеджеров по продажам. Оцени ответы кандидата на ситуационные вопросы.

Кандидат отвечал на следующие вопросы:
{scenarios_and_answers}

Оцени кандидата по следующим критериям (0-100):
- cold_calling_readiness: готовность к холодным звонкам
- objection_handling: работа с возражениями
- closing_ability: умение закрывать сделки
- value_selling: продажа ценности, а не цены
- hunter_vs_farmer: охотник (новые клиенты) или фермер (развитие текущих), 0=фермер, 100=охотник
- money_orientation: денежная мотивация

Также определи:
- overall_sales_score: общая оценка как продажника (0-100)
- recommendation: краткая рекомендация (1-2 предложения)
- concerns: список потенциальных проблем (если есть)

Return valid JSON.""",
        "template_variables": ["scenarios_and_answers"],
        "temperature": 0.5
    },
    "interview_guide": {
        "name": "Interview Guide Generation",
        "description": "Generates personalized interview guide for hiring manager",
        "system_message": None,
        "prompt_template": """Ты опытный HR-бизнес-партнёр. На основе результатов оценки кандидата сгенерируй гайд для финального интервью с руководителем.

Данные кандидата:
- Имя: {name}
- Вакансия: {job_title}
- Скор резюме: {resume_score}/100
- Основная мотивация: {primary_motivation}
- Вторичная мотивация: {secondary_motivation}
- Когнитивный тест: {cognitive_score}/{cognitive_total}
- Поведенческая оценка: {behavioral_summary}
- Личностный профиль: {personality_summary}
- Сейлз-оценка: {sales_score}/100
- Красные флаги: {red_flags}

Сгенерируй JSON:
{{
  "executive_summary": "краткое резюме кандидата для руководителя (3-4 предложения)",
  "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
  "concerns": ["зона риска 1", "зона риска 2", ...],
  "recommended_questions": ["вопрос 1", "вопрос 2", ...],
  "deal_breaker_signals": ["сигнал для отказа 1", ...],
  "hiring_recommendation": "strong_yes / yes / maybe / no"
}}""",
        "template_variables": ["name", "job_title", "resume_score", "primary_motivation", "secondary_motivation", "cognitive_score", "cognitive_total", "behavioral_summary", "personality_summary", "sales_score", "red_flags"],
        "temperature": 0.7
    }
}


async def seed_defaults(db: AsyncSession):
    """Seed default prompts and system settings if not exist."""
    from sqlalchemy import select
    import models

    # Check if prompts already exist
    result = await db.execute(select(models.Prompt).limit(1))
    if result.scalar_one_or_none():
        print("Prompts already seeded, skipping...")
        return

    print("Seeding default prompts...")

    # Seed prompts
    for key, data in DEFAULT_PROMPTS.items():
        prompt = models.Prompt(
            key=key,
            name=data["name"],
            description=data["description"],
            system_message=data["system_message"],
            prompt_template=data["prompt_template"],
            template_variables=data["template_variables"],
            temperature=data["temperature"],
            version=1,
            is_active=True
        )
        db.add(prompt)

    # Seed default system settings
    result = await db.execute(select(models.SystemSettings).limit(1))
    if not result.scalar_one_or_none():
        settings = models.SystemSettings(
            ai_temperature=0.7,
            default_resume_threshold=65,
            default_cognitive_pass=2,
            default_personality_threshold=40,
            default_sales_threshold=40,
            default_screening_criteria={
                "cold_calls": {"expected": True},
                "work_format": {"expected": "office"},
                "salary_expectation": {"max_allowed": 60000}
            }
        )
        db.add(settings)

    await db.commit()
    print("Default data seeded successfully!")
