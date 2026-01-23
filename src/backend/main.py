import os
import json
from contextlib import asynccontextmanager
from openai import AsyncOpenAI
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union, Dict
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db, init_db
import models

# --- Environment and API Key Setup ---
load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")
AI_API_BASE_URL = os.getenv("AI_API_BASE_URL", "https://openrouter.ai/api/v1")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "google/gemini-pro")

if not AI_API_KEY:
    raise ValueError("AI_API_KEY environment variable not set.")

# Instantiate the client with the new configuration
client = AsyncOpenAI(
    api_key=AI_API_KEY,
    base_url=AI_API_BASE_URL,
)

# --- Application Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database
    await init_db()
    yield
    # Shutdown: nothing to do

app = FastAPI(
    title="AI-HR Assistant API",
    description="API for an AI-powered sales recruitment funnel.",
    version="0.2.0",
    lifespan=lifespan
)


# === STAGE 1: JOB POSTING GENERATION ===

JOB_GENERATION_PROMPT = """
Ты — опытный HR-специалист по подбору менеджеров по продажам. Сгенерируй привлекательную вакансию на основе брифа.

**Бриф:**
- Должность: {job_title}
- Компания: {company_name}
- Сегмент продаж: {sales_segment}
- Зарплата: {salary_range}
- План продаж: {sales_target}
- Формат работы: {work_format}
- Дополнительные требования: {additional_requirements}

**Верни JSON-объект со следующей структурой:**
{{
  "job_title_final": "<Финальное название вакансии>",
  "job_description": "<Полный текст вакансии (3-5 абзацев): о компании, обязанности, что предлагаем>",
  "requirements": ["<Требование 1>", "<Требование 2>", ...],
  "nice_to_have": ["<Желательно 1>", "<Желательно 2>", ...],
  "benefits": ["<Преимущество 1>", "<Преимущество 2>", ...],
  "screening_questions": [
    {{"question": "<Вопрос для скрининга>", "type": "yes_no | choice | number", "deal_breaker": true/false}},
    ...
  ],
  "salary_display": "<Как показывать зарплату в объявлении>",
  "tags": ["<тег1>", "<тег2>", ...]
}}
"""

class JobBriefRequest(BaseModel):
    job_title: str = Field(..., json_schema_extra={'example': "Менеджер по продажам B2B"})
    company_name: str = Field(..., json_schema_extra={'example': "ТехноСофт"})
    company_description: Optional[str] = Field(None, json_schema_extra={'example': "IT-компания, разрабатывающая CRM-системы"})
    sales_segment: str = Field(..., json_schema_extra={'example': "B2B SaaS, средний бизнес"})
    salary_range: str = Field(..., json_schema_extra={'example': "80 000 - 150 000 руб + % от продаж"})
    sales_target: Optional[str] = Field(None, json_schema_extra={'example': "500 000 руб/мес выручки"})
    work_format: str = Field(default="office", json_schema_extra={'example': "office / remote / hybrid"})
    additional_requirements: Optional[str] = Field(None, json_schema_extra={'example': "Опыт работы с CRM, английский язык"})

class ScreeningQuestion(BaseModel):
    question: str
    type: str  # yes_no, choice, number
    deal_breaker: bool = False

class JobPostingResponse(BaseModel):
    job_title_final: str
    job_description: str
    requirements: List[str]
    nice_to_have: List[str]
    benefits: List[str]
    screening_questions: List[ScreeningQuestion]
    salary_display: str
    tags: List[str]

@app.post("/v1/jobs/generate", response_model=JobPostingResponse, tags=["Job Posting"])
async def stage1_generate_job_posting(request: JobBriefRequest):
    """
    Stage 1: AI-генерация вакансии на основе брифа.
    """
    prompt = JOB_GENERATION_PROMPT.format(
        job_title=request.job_title,
        company_name=request.company_name,
        sales_segment=request.sales_segment,
        salary_range=request.salary_range,
        sales_target=request.sales_target or "Обсуждается индивидуально",
        work_format=request.work_format,
        additional_requirements=request.additional_requirements or "Нет дополнительных требований"
    )
    try:
        response = await client.chat.completions.create(
            model=AI_MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты HR-эксперт. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        response_data = json.loads(response.choices[0].message.content)
        return JobPostingResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate job posting: {e}")


# === STAGE 2: INITIAL SCREENING ===

SCREENING_QUESTIONS_CRITERIA = {
    "cold_calls": {"expected": True},
    "work_format": {"expected": "office"},
    "salary_expectation": {"max_allowed": 60000}
}

class ScreeningAnswer(BaseModel):
    question_id: str = Field(..., description="Identifier for the question, e.g., 'cold_calls'")
    answer: Union[str, bool, int]

class ScreeningRequest(BaseModel):
    answers: List[ScreeningAnswer]

class ScreeningResponse(BaseModel):
    passed: bool
    details: str

@app.post("/v1/screen/stage2_screening", response_model=ScreeningResponse, tags=["Screening"])
def stage2_screening(request: ScreeningRequest):
    candidate_answers = {ans.question_id: ans.answer for ans in request.answers}
    if candidate_answers.get("cold_calls") != SCREENING_QUESTIONS_CRITERIA["cold_calls"]["expected"]:
        return ScreeningResponse(passed=False, details="Candidate is not willing to make cold calls.")
    if candidate_answers.get("work_format") != SCREENING_QUESTIONS_CRITERIA["work_format"]["expected"]:
        return ScreeningResponse(passed=False, details=f"Candidate prefers '{candidate_answers.get('work_format')}' format, but '{SCREENING_QUESTIONS_CRITERIA['work_format']['expected']}' is required.")
    salary_exp = candidate_answers.get("salary_expectation")
    if not isinstance(salary_exp, int) or salary_exp > SCREENING_QUESTIONS_CRITERIA["salary_expectation"]["max_allowed"]:
        return ScreeningResponse(
            passed=False,
            details=f"Candidate's salary expectation ({salary_exp}) exceeds the maximum allowed ({SCREENING_QUESTIONS_CRITERIA['salary_expectation']['max_allowed']})."
        )
    return ScreeningResponse(passed=True, details="Candidate passed initial screening.")


# === STAGE 3: AI RESUME SCORING ===

RESUME_SCORING_PROMPT_TEMPLATE = """
You are an expert HR manager. Analyze a resume against a job description. Return a JSON object with 'score' (0-100), 'summary' (2-3 sentences), and 'red_flags' (a list of strings).

**Job Description:**
{job_description}

**Candidate's Resume:**
{resume_text}
"""

class ResumeScoringRequest(BaseModel):
    job_description: str
    resume_text: str

class ResumeScoringResponse(BaseModel):
    score: int
    summary: str
    red_flags: List[str]

@app.post("/v1/screen/stage3_resume_scoring", response_model=ResumeScoringResponse, tags=["Screening"])
async def stage3_resume_scoring(request: ResumeScoringRequest):
    prompt = RESUME_SCORING_PROMPT_TEMPLATE.format(
        job_description=request.job_description,
        resume_text=request.resume_text
    )
    try:
        response = await client.chat.completions.create(
            model=AI_MODEL_NAME,
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        response_data = json.loads(response.choices[0].message.content)
        return ResumeScoringResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resume analysis from AI: {e}")


# === STAGE 4: MOTIVATION SURVEY ===

MOTIVATION_SURVEY_PROMPT_TEMPLATE = """
You are an HR psychologist. Analyze the following answers from a candidate to determine their primary and secondary career motivations.

**Candidate's Answers:**
1. Q: Что вас мотивирует в работе больше всего?
   A: {answer_motivation}
2. Q: Почему вы решили сменить работу?
   A: {answer_reason_for_leaving}
3. Q: Как вы относитесь к работе по KPI?
   A: {answer_kpi}

**Your Task:**
Classify the candidate's motivations into one of the primary and one of the secondary categories below.

- **Primary Motivations:** 'Деньги', 'Карьера', 'Стабильность', 'Интерес к задачам'
- **Secondary Motivations:** 'Признание', 'Коллектив', 'Обучение', 'Баланс работы и жизни'

Return a JSON object with the following structure:
{{
  "primary_motivation": "<The single most dominant motivation>",
  "secondary_motivation": "<The second most important motivation>",
  "analysis_summary": "<A 1-2 sentence analysis explaining your reasoning.>"
}}
"""

class MotivationSurveyRequest(BaseModel):
    answer_motivation: str = Field(..., description="Answer to 'What motivates you most in your work?'")
    answer_reason_for_leaving: str = Field(..., description="Answer to 'Why did you decide to change jobs?'")
    answer_kpi: str = Field(..., description="Answer to 'How do you feel about working with KPIs?'")

class MotivationSurveyResponse(BaseModel):
    primary_motivation: str
    secondary_motivation: str
    analysis_summary: str

@app.post("/v1/screen/stage4_motivation_survey", response_model=MotivationSurveyResponse, tags=["Screening"])
async def stage4_motivation_survey(request: MotivationSurveyRequest):
    """
    Performs AI-powered motivation analysis (Stage 4).
    """
    prompt = MOTIVATION_SURVEY_PROMPT_TEMPLATE.format(
        answer_motivation=request.answer_motivation,
        answer_reason_for_leaving=request.answer_reason_for_leaving,
        answer_kpi=request.answer_kpi
    )
    try:
        response = await client.chat.completions.create(
            model=AI_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an HR psychologist. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        response_data = json.loads(response.choices[0].message.content)
        return MotivationSurveyResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get motivation analysis from AI: {e}")


# === STAGE 5: COGNITIVE TEST ===

COGNITIVE_QUIZ_QUESTIONS = [
    {
        "id": "logic_1",
        "question": "Если все Зипы — это Зупы, а некоторые Зупы — это Зопы, то некоторые Зипы обязательно являются Зопами.",
        "options": ["Правда", "Ложь"],
        "correct_answer": "Ложь"
    },
    {
        "id": "math_1",
        "question": "Ручка и блокнот вместе стоят 110 рублей. Блокнот стоит на 100 рублей дороже ручки. Сколько стоит ручка?",
        "options": ["5 рублей", "10 рублей", "15 рублей", "Невозможно определить"],
        "correct_answer": "5 рублей"
    },
    {
        "id": "attention_1",
        "question": "Найдите и посчитайте, сколько раз в следующем предложении встречается буква 'о': 'Огромный опоссум озадаченно оглядывался по сторонам, поедая сочное оранжевое яблоко.'",
        "options": ["9", "10", "11", "12"],
        "correct_answer": "11"
    }
]

class CognitiveQuestion(BaseModel):
    id: str
    question: str
    options: List[str]

class CandidateAnswer(BaseModel):
    question_id: str
    answer: str

class CognitiveTestSubmission(BaseModel):
    answers: List[CandidateAnswer]

class CognitiveTestResult(BaseModel):
    score: int
    total: int
    passed: bool

@app.get("/v1/screen/stage5_cognitive_test/questions", response_model=List[CognitiveQuestion], tags=["Screening"])
def get_cognitive_test_questions():
    """
    Provides the list of questions for the cognitive test (Stage 5).
    """
    return [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in COGNITIVE_QUIZ_QUESTIONS]

@app.post("/v1/screen/stage5_cognitive_test", response_model=CognitiveTestResult, tags=["Screening"])
def submit_cognitive_test(submission: CognitiveTestSubmission):
    """
    Scores the submitted answers for the cognitive test (Stage 5).
    """
    correct_answers_map = {q["id"]: q["correct_answer"] for q in COGNITIVE_QUIZ_QUESTIONS}
    score = 0
    for answer in submission.answers:
        if correct_answers_map.get(answer.question_id) == answer.answer:
            score += 1

    total = len(COGNITIVE_QUIZ_QUESTIONS)
    passed = score >= (total - 1) # Allow one mistake

    return CognitiveTestResult(score=score, total=total, passed=passed)


# === STAGE 6: BEHAVIORAL CHAT (AI-РЕЗАЛТ) ===

BEHAVIORAL_QUESTIONS = [
    "Здравствуйте! Давайте начнем. Расскажите о вашем самом большом достижении в продажах, которым вы гордитесь, и что конкретно вы сделали для его достижения?",
    "Спасибо. Теперь расскажите о ситуации, когда вы не смогли достичь поставленной цели или провалили сделку. Что пошло не так и чему вы научились?",
    "Интересно. Опишите случай, когда вам пришлось работать с очень сложным или недовольным клиентом. Как вы справились с ситуацией?",
    "Хорошо. Представьте, что в середине квартала вы понимаете, что отстаете от плана продаж. Какие три конкретных шага вы предпримете?",
    "Последний вопрос. Что для вас важнее в работе: достичь цели любой ценой или следовать этическим принципам и правилам компании? Почему?"
]

FINAL_ASSESSMENT_PROMPT = """
Ты — опытный HR-директор. Проанализируй диалог с кандидатом и верни JSON-объект с оценками по 5 компетенциям (proactivity, honesty, resilience, structure, motivation) и итоговым резюме 'final_summary'.

**Диалог:**
{chat_history}
"""

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class BehavioralChatRequest(BaseModel):
    conversation: List[ChatMessage]

class BehavioralChatResponse(BaseModel):
    conversation: List[ChatMessage]
    assessment: Optional[dict] = None

@app.post("/v1/screen/stage6_behavioral_chat", response_model=BehavioralChatResponse, tags=["Screening"])
async def stage6_behavioral_chat(request: BehavioralChatRequest):
    conversation = request.conversation
    user_message_count = sum(1 for msg in conversation if msg.role == 'user')

    if not conversation:
        next_question = BEHAVIORAL_QUESTIONS[0]
        conversation.append(ChatMessage(role="assistant", content=next_question))
        return BehavioralChatResponse(conversation=conversation)

    if user_message_count < len(BEHAVIORAL_QUESTIONS):
        next_question = BEHAVIORAL_QUESTIONS[user_message_count]
        conversation.append(ChatMessage(role="assistant", content=next_question))
        return BehavioralChatResponse(conversation=conversation)
    else:
        chat_history_str = "\n".join([f"{msg.role.capitalize()}: {msg.content}" for msg in conversation])
        prompt = FINAL_ASSESSMENT_PROMPT.format(chat_history=chat_history_str)
        try:
            response = await client.chat.completions.create(
                model=AI_MODEL_NAME,
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.5,
            )
            assessment = json.loads(response.choices[0].message.content)
            return BehavioralChatResponse(conversation=conversation, assessment=assessment)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get assessment from AI: {e}")

# === JOBS CRUD ===

class JobCreate(BaseModel):
    """Request to create and save a job"""
    brief: JobBriefRequest
    generated: JobPostingResponse

class JobOut(BaseModel):
    """Job response model"""
    id: int
    job_title: str
    company_name: str
    job_title_final: str
    job_description: str
    requirements: List[str]
    nice_to_have: List[str]
    benefits: List[str]
    screening_questions: List[dict]
    salary_display: str
    tags: List[str]
    is_active: bool
    candidates_count: int = 0

    class Config:
        from_attributes = True

@app.post("/v1/jobs", response_model=JobOut, tags=["Jobs"])
async def create_job(request: JobCreate, db: AsyncSession = Depends(get_db)):
    """Создать и сохранить вакансию в БД."""
    job = models.Job(
        # Brief data
        job_title=request.brief.job_title,
        company_name=request.brief.company_name,
        company_description=request.brief.company_description,
        sales_segment=request.brief.sales_segment,
        salary_range=request.brief.salary_range,
        sales_target=request.brief.sales_target,
        work_format=request.brief.work_format,
        additional_requirements=request.brief.additional_requirements,
        # Generated data
        job_title_final=request.generated.job_title_final,
        job_description=request.generated.job_description,
        requirements=request.generated.requirements,
        nice_to_have=request.generated.nice_to_have,
        benefits=request.generated.benefits,
        screening_questions=[q.model_dump() for q in request.generated.screening_questions],
        salary_display=request.generated.salary_display,
        tags=request.generated.tags,
        # Default screening criteria
        screening_criteria=SCREENING_QUESTIONS_CRITERIA,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return JobOut(
        id=job.id,
        job_title=job.job_title,
        company_name=job.company_name,
        job_title_final=job.job_title_final,
        job_description=job.job_description,
        requirements=job.requirements,
        nice_to_have=job.nice_to_have,
        benefits=job.benefits,
        screening_questions=job.screening_questions,
        salary_display=job.salary_display,
        tags=job.tags,
        is_active=job.is_active,
        candidates_count=0
    )

@app.get("/v1/jobs", response_model=List[JobOut], tags=["Jobs"])
async def list_jobs(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    """Получить список вакансий."""
    query = select(models.Job).options(selectinload(models.Job.candidates))
    if active_only:
        query = query.where(models.Job.is_active == True)
    result = await db.execute(query.order_by(models.Job.created_at.desc()))
    jobs = result.scalars().all()

    return [
        JobOut(
            id=job.id,
            job_title=job.job_title,
            company_name=job.company_name,
            job_title_final=job.job_title_final,
            job_description=job.job_description,
            requirements=job.requirements or [],
            nice_to_have=job.nice_to_have or [],
            benefits=job.benefits or [],
            screening_questions=job.screening_questions or [],
            salary_display=job.salary_display,
            tags=job.tags or [],
            is_active=job.is_active,
            candidates_count=len(job.candidates) if hasattr(job, 'candidates') else 0
        )
        for job in jobs
    ]

@app.get("/v1/jobs/{job_id}", response_model=JobOut, tags=["Jobs"])
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Получить вакансию по ID."""
    result = await db.execute(
        select(models.Job)
        .options(selectinload(models.Job.candidates))
        .where(models.Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut(
        id=job.id,
        job_title=job.job_title,
        company_name=job.company_name,
        job_title_final=job.job_title_final,
        job_description=job.job_description,
        requirements=job.requirements or [],
        nice_to_have=job.nice_to_have or [],
        benefits=job.benefits or [],
        screening_questions=job.screening_questions or [],
        salary_display=job.salary_display,
        tags=job.tags or [],
        is_active=job.is_active,
        candidates_count=0
    )


# === CANDIDATES CRUD ===

class CandidateCreate(BaseModel):
    """Request to create a candidate session"""
    job_id: int
    name: Optional[str] = None
    email: Optional[str] = None

class CandidateOut(BaseModel):
    """Candidate response model"""
    id: int
    job_id: int
    name: Optional[str]
    status: str
    current_stage: str
    screening_passed: Optional[bool]
    resume_score: Optional[int]
    resume_passed: Optional[bool]
    primary_motivation: Optional[str]
    secondary_motivation: Optional[str]
    cognitive_score: Optional[int]
    cognitive_total: Optional[int]
    cognitive_passed: Optional[bool]
    interview_assessment: Optional[dict]
    created_at: str

    class Config:
        from_attributes = True

class CandidateDetailOut(CandidateOut):
    """Detailed candidate data for HR"""
    resume_summary: Optional[str]
    resume_red_flags: Optional[List[str]]
    motivation_summary: Optional[str]
    interview_conversation: Optional[List[dict]]

@app.post("/v1/candidates", response_model=CandidateOut, tags=["Candidates"])
async def create_candidate(request: CandidateCreate, db: AsyncSession = Depends(get_db)):
    """Создать сессию кандидата для прохождения отбора."""
    # Verify job exists
    job_result = await db.execute(
        select(models.Job).where(models.Job.id == request.job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate = models.Candidate(
        job_id=request.job_id,
        name=request.name,
        email=request.email,
        status="in_progress",
        current_stage="screening"
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    return CandidateOut(
        id=candidate.id,
        job_id=candidate.job_id,
        name=candidate.name,
        status=candidate.status,
        current_stage=candidate.current_stage,
        screening_passed=candidate.screening_passed,
        resume_score=candidate.resume_score,
        resume_passed=candidate.resume_passed,
        primary_motivation=candidate.primary_motivation,
        secondary_motivation=candidate.secondary_motivation,
        cognitive_score=candidate.cognitive_score,
        cognitive_total=candidate.cognitive_total,
        cognitive_passed=candidate.cognitive_passed,
        interview_assessment=candidate.interview_assessment,
        created_at=candidate.created_at.isoformat()
    )

@app.get("/v1/candidates", response_model=List[CandidateOut], tags=["Candidates"])
async def list_candidates(
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список кандидатов (для HR)."""
    query = select(models.Candidate)
    if job_id:
        query = query.where(models.Candidate.job_id == job_id)
    if status:
        query = query.where(models.Candidate.status == status)

    result = await db.execute(query.order_by(models.Candidate.created_at.desc()))
    candidates = result.scalars().all()

    return [
        CandidateOut(
            id=c.id,
            job_id=c.job_id,
            name=c.name,
            status=c.status,
            current_stage=c.current_stage,
            screening_passed=c.screening_passed,
            resume_score=c.resume_score,
            resume_passed=c.resume_passed,
            primary_motivation=c.primary_motivation,
            secondary_motivation=c.secondary_motivation,
            cognitive_score=c.cognitive_score,
            cognitive_total=c.cognitive_total,
            cognitive_passed=c.cognitive_passed,
            interview_assessment=c.interview_assessment,
            created_at=c.created_at.isoformat()
        )
        for c in candidates
    ]

@app.get("/v1/candidates/{candidate_id}", response_model=CandidateDetailOut, tags=["Candidates"])
async def get_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    """Получить детальную информацию о кандидате (для HR)."""
    result = await db.execute(
        select(models.Candidate).where(models.Candidate.id == candidate_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return CandidateDetailOut(
        id=c.id,
        job_id=c.job_id,
        name=c.name,
        status=c.status,
        current_stage=c.current_stage,
        screening_passed=c.screening_passed,
        resume_score=c.resume_score,
        resume_passed=c.resume_passed,
        resume_summary=c.resume_summary,
        resume_red_flags=c.resume_red_flags,
        primary_motivation=c.primary_motivation,
        secondary_motivation=c.secondary_motivation,
        motivation_summary=c.motivation_summary,
        cognitive_score=c.cognitive_score,
        cognitive_total=c.cognitive_total,
        cognitive_passed=c.cognitive_passed,
        interview_assessment=c.interview_assessment,
        interview_conversation=c.interview_conversation,
        created_at=c.created_at.isoformat()
    )

class CandidateStageUpdate(BaseModel):
    """Update candidate stage results"""
    stage: str
    data: dict
    passed: Optional[bool] = None

@app.patch("/v1/candidates/{candidate_id}/stage", response_model=CandidateOut, tags=["Candidates"])
async def update_candidate_stage(
    candidate_id: int,
    update: CandidateStageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить результаты этапа для кандидата."""
    result = await db.execute(
        select(models.Candidate).where(models.Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    stage = update.stage
    data = update.data

    if stage == "screening":
        candidate.screening_data = data
        candidate.screening_passed = update.passed
        if update.passed:
            candidate.current_stage = "resume"
        else:
            candidate.status = "rejected"
            candidate.rejection_stage = "screening"

    elif stage == "resume":
        candidate.resume_text = data.get("resume_text")
        candidate.resume_score = data.get("score")
        candidate.resume_summary = data.get("summary")
        candidate.resume_red_flags = data.get("red_flags")
        candidate.resume_passed = update.passed
        if update.passed:
            candidate.current_stage = "motivation"
        else:
            candidate.status = "rejected"
            candidate.rejection_stage = "resume"

    elif stage == "motivation":
        candidate.motivation_data = data
        candidate.primary_motivation = data.get("primary_motivation")
        candidate.secondary_motivation = data.get("secondary_motivation")
        candidate.motivation_summary = data.get("analysis_summary")
        candidate.current_stage = "cognitive"

    elif stage == "cognitive":
        candidate.cognitive_score = data.get("score")
        candidate.cognitive_total = data.get("total")
        candidate.cognitive_passed = update.passed
        if update.passed:
            candidate.current_stage = "interview"
        else:
            candidate.status = "rejected"
            candidate.rejection_stage = "cognitive"

    elif stage == "interview":
        candidate.interview_conversation = data.get("conversation")
        candidate.interview_assessment = data.get("assessment")
        candidate.current_stage = "personality"  # Продолжаем к личностному профилю

    elif stage == "personality":
        candidate.personality_profile = data.get("profile")
        candidate.personality_summary = data.get("summary")
        candidate.personality_score = data.get("sales_fit_score")
        # Собираем красные флаги
        existing_flags = candidate.red_flags or []
        new_flags = data.get("red_flags", [])
        candidate.red_flags = list(set(existing_flags + new_flags))
        if update.passed:
            candidate.current_stage = "sales"
        else:
            candidate.status = "rejected"
            candidate.rejection_stage = "personality"

    elif stage == "sales":
        candidate.sales_data = data
        candidate.sales_score = data.get("overall_sales_score")
        candidate.sales_concerns = data.get("concerns")
        # Добавляем concerns в красные флаги
        existing_flags = candidate.red_flags or []
        concerns = data.get("concerns", [])
        candidate.red_flags = list(set(existing_flags + concerns))
        if update.passed:
            candidate.current_stage = "ready_for_final"  # Готов к финальному интервью
        else:
            candidate.status = "rejected"
            candidate.rejection_stage = "sales"

    elif stage == "final_interview":
        # После интервью с руководителем
        candidate.current_stage = "offer_pending"

    elif stage == "offer":
        candidate.status = "completed"
        candidate.current_stage = "hired"

    await db.commit()
    await db.refresh(candidate)

    return CandidateOut(
        id=candidate.id,
        job_id=candidate.job_id,
        name=candidate.name,
        status=candidate.status,
        current_stage=candidate.current_stage,
        screening_passed=candidate.screening_passed,
        resume_score=candidate.resume_score,
        resume_passed=candidate.resume_passed,
        primary_motivation=candidate.primary_motivation,
        secondary_motivation=candidate.secondary_motivation,
        cognitive_score=candidate.cognitive_score,
        cognitive_total=candidate.cognitive_total,
        cognitive_passed=candidate.cognitive_passed,
        interview_assessment=candidate.interview_assessment,
        created_at=candidate.created_at.isoformat()
    )


# === STATISTICS ===

class StatsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    total_candidates: int
    completed_candidates: int
    rejected_candidates: int
    in_progress_candidates: int
    conversion_rate: float

@app.get("/v1/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Получить статистику для дашборда HR."""
    jobs_result = await db.execute(select(models.Job))
    all_jobs = jobs_result.scalars().all()

    candidates_result = await db.execute(select(models.Candidate))
    all_candidates = candidates_result.scalars().all()

    total_jobs = len(all_jobs)
    active_jobs = len([j for j in all_jobs if j.is_active])
    total_candidates = len(all_candidates)
    completed = len([c for c in all_candidates if c.status == "completed"])
    rejected = len([c for c in all_candidates if c.status == "rejected"])
    in_progress = len([c for c in all_candidates if c.status == "in_progress"])
    conversion = (completed / total_candidates * 100) if total_candidates > 0 else 0

    return StatsResponse(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_candidates=total_candidates,
        completed_candidates=completed,
        rejected_candidates=rejected,
        in_progress_candidates=in_progress,
        conversion_rate=round(conversion, 1)
    )


# === STAGE 7: PERSONALITY PROFILE (ТУЛС) ===

PERSONALITY_QUESTIONS = [
    # Настойчивость (persistence)
    {"id": "pers_1", "text": "Когда клиент говорит 'нет', я обычно:", "scale": "persistence",
     "options": [
         {"value": 1, "text": "Принимаю отказ и перехожу к следующему"},
         {"value": 3, "text": "Пробую один раз переубедить"},
         {"value": 5, "text": "Ищу новый подход и продолжаю работу"}
     ]},
    {"id": "pers_2", "text": "Если цель месяца кажется недостижимой, я:", "scale": "persistence",
     "options": [
         {"value": 1, "text": "Смиряюсь и работаю в комфортном режиме"},
         {"value": 3, "text": "Стараюсь, но не перерабатываю"},
         {"value": 5, "text": "Удваиваю усилия до последнего дня"}
     ]},
    # Стрессоустойчивость (stress_resistance)
    {"id": "stress_1", "text": "После серии отказов подряд я:", "scale": "stress_resistance",
     "options": [
         {"value": 1, "text": "Чувствую упадок сил и мотивации"},
         {"value": 3, "text": "Делаю паузу, чтобы восстановиться"},
         {"value": 5, "text": "Продолжаю работать, это часть процесса"}
     ]},
    {"id": "stress_2", "text": "Когда руководитель критикует мою работу, я:", "scale": "stress_resistance",
     "options": [
         {"value": 1, "text": "Расстраиваюсь и долго переживаю"},
         {"value": 3, "text": "Принимаю к сведению, но это неприятно"},
         {"value": 5, "text": "Благодарю за обратную связь и исправляю"}
     ]},
    # Энергия (energy)
    {"id": "energy_1", "text": "Мой типичный рабочий темп:", "scale": "energy",
     "options": [
         {"value": 1, "text": "Размеренный, без спешки"},
         {"value": 3, "text": "Средний, с пиками активности"},
         {"value": 5, "text": "Высокий, я люблю динамику"}
     ]},
    {"id": "energy_2", "text": "После 8-часового рабочего дня я:", "scale": "energy",
     "options": [
         {"value": 1, "text": "Полностью вымотан"},
         {"value": 3, "text": "Устал, но это нормально"},
         {"value": 5, "text": "Ещё есть силы на дополнительные дела"}
     ]},
    # Общительность (sociability)
    {"id": "social_1", "text": "Общение с незнакомыми людьми для меня:", "scale": "sociability",
     "options": [
         {"value": 1, "text": "Стресс, я избегаю этого"},
         {"value": 3, "text": "Нейтрально, когда нужно - общаюсь"},
         {"value": 5, "text": "Удовольствие, легко нахожу общий язык"}
     ]},
    {"id": "social_2", "text": "На корпоративе или нетворкинге я:", "scale": "sociability",
     "options": [
         {"value": 1, "text": "Стою в стороне или ухожу рано"},
         {"value": 3, "text": "Общаюсь с знакомыми коллегами"},
         {"value": 5, "text": "Знакомлюсь с максимумом людей"}
     ]},
    # Честность (honesty)
    {"id": "honest_1", "text": "Если продукт не подходит клиенту, я:", "scale": "honesty",
     "options": [
         {"value": 5, "text": "Честно скажу и предложу альтернативу"},
         {"value": 3, "text": "Постараюсь найти хоть какую-то пользу"},
         {"value": 1, "text": "Всё равно попробую продать"}
     ]},
    {"id": "honest_2", "text": "При заполнении отчётов я:", "scale": "honesty",
     "options": [
         {"value": 5, "text": "Всегда указываю реальные цифры"},
         {"value": 3, "text": "Иногда округляю в свою пользу"},
         {"value": 1, "text": "Подгоняю под нужный результат"}
     ]},
    # Командность (teamwork)
    {"id": "team_1", "text": "Когда коллега просит помочь с его клиентом, я:", "scale": "teamwork",
     "options": [
         {"value": 1, "text": "Отказываюсь - у меня свои задачи"},
         {"value": 3, "text": "Помогаю, если есть время"},
         {"value": 5, "text": "Всегда помогаю, успех команды важнее"}
     ]},
    {"id": "team_2", "text": "Лучшие результаты я показываю:", "scale": "teamwork",
     "options": [
         {"value": 1, "text": "Работая полностью самостоятельно"},
         {"value": 3, "text": "В небольшой команде"},
         {"value": 5, "text": "В тесной командной работе"}
     ]},
    # Готовность к рутине (routine_tolerance)
    {"id": "routine_1", "text": "Делать 50+ звонков в день для меня:", "scale": "routine_tolerance",
     "options": [
         {"value": 1, "text": "Невыносимо, это убивает мотивацию"},
         {"value": 3, "text": "Терпимо, если есть результат"},
         {"value": 5, "text": "Нормально, это часть работы"}
     ]},
    {"id": "routine_2", "text": "Заполнение CRM после каждого контакта:", "scale": "routine_tolerance",
     "options": [
         {"value": 1, "text": "Бесполезная трата времени"},
         {"value": 3, "text": "Необходимость, делаю без энтузиазма"},
         {"value": 5, "text": "Важно для системности работы"}
     ]},
]

PERSONALITY_SCALES = ["persistence", "stress_resistance", "energy", "sociability", "honesty", "teamwork", "routine_tolerance"]

class PersonalityQuestion(BaseModel):
    id: str
    text: str
    scale: str
    options: List[dict]

class PersonalityAnswer(BaseModel):
    question_id: str
    value: int

class PersonalityTestRequest(BaseModel):
    answers: List[PersonalityAnswer]

class PersonalityProfile(BaseModel):
    persistence: int = Field(..., ge=0, le=100, description="Настойчивость")
    stress_resistance: int = Field(..., ge=0, le=100, description="Стрессоустойчивость")
    energy: int = Field(..., ge=0, le=100, description="Энергия")
    sociability: int = Field(..., ge=0, le=100, description="Общительность")
    honesty: int = Field(..., ge=0, le=100, description="Честность")
    teamwork: int = Field(..., ge=0, le=100, description="Командность")
    routine_tolerance: int = Field(..., ge=0, le=100, description="Готовность к рутине")
    summary: str
    red_flags: List[str]
    sales_fit_score: int = Field(..., ge=0, le=100)

@app.get("/v1/screen/stage7_personality/questions", response_model=List[PersonalityQuestion], tags=["Screening"])
def get_personality_questions():
    """Stage 7: Получить вопросы личностного профиля."""
    return PERSONALITY_QUESTIONS

@app.post("/v1/screen/stage7_personality", response_model=PersonalityProfile, tags=["Screening"])
def stage7_personality_test(request: PersonalityTestRequest):
    """Stage 7: Рассчитать личностный профиль по ответам."""
    # Собираем баллы по шкалам
    scale_scores = {scale: [] for scale in PERSONALITY_SCALES}
    question_map = {q["id"]: q["scale"] for q in PERSONALITY_QUESTIONS}

    for answer in request.answers:
        scale = question_map.get(answer.question_id)
        if scale:
            scale_scores[scale].append(answer.value)

    # Нормализуем в 0-100
    profile = {}
    for scale in PERSONALITY_SCALES:
        scores = scale_scores[scale]
        if scores:
            avg = sum(scores) / len(scores)
            profile[scale] = int((avg - 1) / 4 * 100)  # 1-5 -> 0-100
        else:
            profile[scale] = 50  # default

    # Определяем красные флаги
    red_flags = []
    if profile["persistence"] < 40:
        red_flags.append("Низкая настойчивость - может сдаваться после первых отказов")
    if profile["stress_resistance"] < 40:
        red_flags.append("Низкая стрессоустойчивость - риск выгорания")
    if profile["honesty"] < 40:
        red_flags.append("Возможны проблемы с честностью в отчётности")
    if profile["routine_tolerance"] < 30:
        red_flags.append("Низкая толерантность к рутине - может быстро уволиться")

    # Sales fit score (взвешенная оценка для продаж)
    sales_fit = int(
        profile["persistence"] * 0.25 +
        profile["stress_resistance"] * 0.20 +
        profile["energy"] * 0.15 +
        profile["sociability"] * 0.15 +
        profile["honesty"] * 0.10 +
        profile["routine_tolerance"] * 0.15
    )

    # Генерируем саммари
    strengths = [scale for scale in PERSONALITY_SCALES if profile[scale] >= 70]
    weaknesses = [scale for scale in PERSONALITY_SCALES if profile[scale] < 40]

    summary_parts = []
    if strengths:
        summary_parts.append(f"Сильные стороны: {', '.join(strengths)}")
    if weaknesses:
        summary_parts.append(f"Зоны развития: {', '.join(weaknesses)}")
    summary_parts.append(f"Общая оценка для продаж: {sales_fit}/100")

    return PersonalityProfile(
        **profile,
        summary=". ".join(summary_parts),
        red_flags=red_flags,
        sales_fit_score=sales_fit
    )


# === STAGE 8: SALES-SPECIFIC BLOCK ===

SALES_SCENARIOS = [
    {
        "id": "scenario_1",
        "type": "situation",
        "text": "Клиент говорит: 'Мне нужно подумать'. Ваши действия?",
        "evaluation_criteria": ["work_with_objections", "persistence", "closing_skills"]
    },
    {
        "id": "scenario_2",
        "type": "situation",
        "text": "Вы выявили, что ваш продукт дороже конкурента на 30%. Как будете продавать?",
        "evaluation_criteria": ["value_selling", "confidence", "product_knowledge"]
    },
    {
        "id": "scenario_3",
        "type": "situation",
        "text": "ЛПР постоянно переносит встречу уже третий раз. Что делать?",
        "evaluation_criteria": ["persistence", "creativity", "time_management"]
    },
    {
        "id": "scenario_4",
        "type": "motivation",
        "text": "Что мотивирует вас в продажах больше всего?",
        "evaluation_criteria": ["money_motivation", "achievement_motivation", "growth_motivation"]
    },
    {
        "id": "scenario_5",
        "type": "experience",
        "text": "Опишите вашу самую крупную сделку. Как вы её закрыли?",
        "evaluation_criteria": ["deal_experience", "sales_process", "result_orientation"]
    },
    {
        "id": "scenario_6",
        "type": "situation",
        "text": "Клиент требует скидку 50%, иначе уйдёт к конкуренту. Ваши действия?",
        "evaluation_criteria": ["negotiation", "value_protection", "decision_making"]
    },
    {
        "id": "scenario_7",
        "type": "cold_calling",
        "text": "Как вы начинаете холодный звонок? Приведите пример первых 30 секунд.",
        "evaluation_criteria": ["cold_calling_skills", "hook_creation", "confidence"]
    },
    {
        "id": "scenario_8",
        "type": "objection",
        "text": "Клиент: 'У нас уже есть поставщик, нас всё устраивает'. Ваш ответ?",
        "evaluation_criteria": ["work_with_objections", "competitive_positioning", "curiosity"]
    },
]

SALES_EVALUATION_PROMPT = """
Ты опытный HR-специалист по найму менеджеров по продажам. Оцени ответы кандидата на ситуационные вопросы.

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

Верни JSON:
{{
    "cold_calling_readiness": number,
    "objection_handling": number,
    "closing_ability": number,
    "value_selling": number,
    "hunter_vs_farmer": number,
    "money_orientation": number,
    "overall_sales_score": number,
    "recommendation": "string",
    "concerns": ["string"]
}}
"""

class SalesScenario(BaseModel):
    id: str
    type: str
    text: str

class SalesAnswer(BaseModel):
    scenario_id: str
    answer: str

class SalesBlockRequest(BaseModel):
    answers: List[SalesAnswer]

class SalesBlockResponse(BaseModel):
    cold_calling_readiness: int
    objection_handling: int
    closing_ability: int
    value_selling: int
    hunter_vs_farmer: int
    money_orientation: int
    overall_sales_score: int
    recommendation: str
    concerns: List[str]

@app.get("/v1/screen/stage8_sales/scenarios", response_model=List[SalesScenario], tags=["Screening"])
def get_sales_scenarios():
    """Stage 8: Получить ситуационные вопросы для сейлзов."""
    return [SalesScenario(id=s["id"], type=s["type"], text=s["text"]) for s in SALES_SCENARIOS]

@app.post("/v1/screen/stage8_sales", response_model=SalesBlockResponse, tags=["Screening"])
async def stage8_sales_block(request: SalesBlockRequest):
    """Stage 8: AI-оценка ответов на сейлз-кейсы."""
    scenario_map = {s["id"]: s["text"] for s in SALES_SCENARIOS}

    scenarios_text = "\n\n".join([
        f"Вопрос: {scenario_map.get(a.scenario_id, 'Unknown')}\nОтвет: {a.answer}"
        for a in request.answers
    ])

    prompt = SALES_EVALUATION_PROMPT.format(scenarios_and_answers=scenarios_text)

    response = await client.chat.completions.create(
        model=AI_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return SalesBlockResponse(
        cold_calling_readiness=result.get("cold_calling_readiness", 50),
        objection_handling=result.get("objection_handling", 50),
        closing_ability=result.get("closing_ability", 50),
        value_selling=result.get("value_selling", 50),
        hunter_vs_farmer=result.get("hunter_vs_farmer", 50),
        money_orientation=result.get("money_orientation", 50),
        overall_sales_score=result.get("overall_sales_score", 50),
        recommendation=result.get("recommendation", ""),
        concerns=result.get("concerns", [])
    )


# === STAGE 12: AI INTERVIEW GUIDE ===

INTERVIEW_GUIDE_PROMPT = """
Ты опытный HR-бизнес-партнёр. На основе результатов оценки кандидата сгенерируй гайд для финального интервью с руководителем.

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

Сгенерируй:
1. executive_summary: краткое резюме кандидата для руководителя (3-4 предложения)
2. strengths: список сильных сторон (3-5 пунктов)
3. concerns: список зон риска для проверки (2-4 пункта)
4. recommended_questions: 5-7 персонализированных вопросов для интервью, направленных на проверку слабых зон
5. deal_breaker_signals: на что обратить внимание - сигналы для отказа
6. hiring_recommendation: рекомендация (strong_yes / yes / maybe / no) с обоснованием

Верни JSON.
"""

class InterviewGuideRequest(BaseModel):
    candidate_id: int

class InterviewGuideResponse(BaseModel):
    candidate_name: str
    job_title: str
    executive_summary: str
    strengths: List[str]
    concerns: List[str]
    recommended_questions: List[str]
    deal_breaker_signals: List[str]
    hiring_recommendation: str
    recommendation_reasoning: str

@app.post("/v1/screen/stage12_interview_guide", response_model=InterviewGuideResponse, tags=["Screening"])
async def stage12_interview_guide(request: InterviewGuideRequest, db: AsyncSession = Depends(get_db)):
    """Stage 12: Генерация AI-гайда для финального интервью."""
    # Получаем кандидата со всеми данными
    result = await db.execute(
        select(models.Candidate).where(models.Candidate.id == request.candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Получаем вакансию
    job_result = await db.execute(
        select(models.Job).where(models.Job.id == candidate.job_id)
    )
    job = job_result.scalar_one_or_none()

    # Собираем данные для промпта
    prompt = INTERVIEW_GUIDE_PROMPT.format(
        name=candidate.name or "Неизвестно",
        job_title=job.job_title_final if job else "Менеджер по продажам",
        resume_score=candidate.resume_score or "Не оценено",
        primary_motivation=candidate.primary_motivation or "Не определена",
        secondary_motivation=candidate.secondary_motivation or "Не определена",
        cognitive_score=candidate.cognitive_score or "N/A",
        cognitive_total=candidate.cognitive_total or 3,
        behavioral_summary=candidate.interview_assessment.get("final_summary", "Не пройдено") if candidate.interview_assessment else "Не пройдено",
        personality_summary=candidate.personality_summary or "Не пройдено",
        sales_score=candidate.sales_score or "Не оценено",
        red_flags=", ".join(candidate.red_flags or []) if candidate.red_flags else "Не выявлено"
    )

    response = await client.chat.completions.create(
        model=AI_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return InterviewGuideResponse(
        candidate_name=candidate.name or "Неизвестно",
        job_title=job.job_title_final if job else "Менеджер по продажам",
        executive_summary=result.get("executive_summary", ""),
        strengths=result.get("strengths", []),
        concerns=result.get("concerns", []),
        recommended_questions=result.get("recommended_questions", []),
        deal_breaker_signals=result.get("deal_breaker_signals", []),
        hiring_recommendation=result.get("hiring_recommendation", "maybe"),
        recommendation_reasoning=result.get("recommendation_reasoning", "")
    )


# === STAGE 13: OFFER MANAGEMENT ===

class OfferStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"

class OfferCreate(BaseModel):
    candidate_id: int
    salary_offered: int
    start_date: str
    probation_period_months: int = 3
    additional_terms: Optional[str] = None

class OfferOut(BaseModel):
    id: int
    candidate_id: int
    candidate_name: str
    job_title: str
    salary_offered: int
    start_date: str
    probation_period_months: int
    additional_terms: Optional[str]
    status: OfferStatus
    created_at: str
    updated_at: str

class OfferUpdate(BaseModel):
    status: OfferStatus

# Для простоты храним офферы в памяти (в реальности - в БД)
# TODO: Добавить модель Offer в models.py
offers_storage: Dict[int, dict] = {}
offer_counter = 0

@app.post("/v1/offers", response_model=OfferOut, tags=["Offers"])
async def create_offer(request: OfferCreate, db: AsyncSession = Depends(get_db)):
    """Stage 13: Создать оффер для кандидата."""
    global offer_counter

    # Проверяем кандидата
    result = await db.execute(
        select(models.Candidate).where(models.Candidate.id == request.candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Получаем вакансию
    job_result = await db.execute(
        select(models.Job).where(models.Job.id == candidate.job_id)
    )
    job = job_result.scalar_one_or_none()

    offer_counter += 1
    now = datetime.utcnow().isoformat()

    offer = {
        "id": offer_counter,
        "candidate_id": request.candidate_id,
        "candidate_name": candidate.name or "Неизвестно",
        "job_title": job.job_title_final if job else "Позиция",
        "salary_offered": request.salary_offered,
        "start_date": request.start_date,
        "probation_period_months": request.probation_period_months,
        "additional_terms": request.additional_terms,
        "status": OfferStatus.draft,
        "created_at": now,
        "updated_at": now
    }

    offers_storage[offer_counter] = offer
    return OfferOut(**offer)

@app.get("/v1/offers", response_model=List[OfferOut], tags=["Offers"])
def list_offers(candidate_id: Optional[int] = None):
    """Получить список офферов."""
    offers = list(offers_storage.values())
    if candidate_id:
        offers = [o for o in offers if o["candidate_id"] == candidate_id]
    return [OfferOut(**o) for o in offers]

@app.patch("/v1/offers/{offer_id}", response_model=OfferOut, tags=["Offers"])
def update_offer_status(offer_id: int, update: OfferUpdate):
    """Обновить статус оффера."""
    if offer_id not in offers_storage:
        raise HTTPException(status_code=404, detail="Offer not found")

    offers_storage[offer_id]["status"] = update.status
    offers_storage[offer_id]["updated_at"] = datetime.utcnow().isoformat()

    return OfferOut(**offers_storage[offer_id])


# === STAGE 14: ONBOARDING ===

ONBOARDING_CHECKLIST_TEMPLATE = [
    {"id": "docs", "title": "Документы оформлены", "category": "hr"},
    {"id": "equipment", "title": "Оборудование выдано", "category": "hr"},
    {"id": "access", "title": "Доступы настроены (CRM, почта, телефония)", "category": "it"},
    {"id": "intro_meeting", "title": "Встреча с командой проведена", "category": "team"},
    {"id": "product_training", "title": "Обучение по продукту пройдено", "category": "training"},
    {"id": "sales_training", "title": "Тренинг по продажам пройден", "category": "training"},
    {"id": "first_calls", "title": "Первые звонки под наблюдением", "category": "practice"},
    {"id": "first_meeting", "title": "Первая встреча с клиентом", "category": "practice"},
    {"id": "crm_filled", "title": "CRM заполняется корректно", "category": "practice"},
    {"id": "week1_review", "title": "Ревью первой недели", "category": "review"},
    {"id": "month1_review", "title": "Ревью первого месяца", "category": "review"},
]

class OnboardingChecklistItem(BaseModel):
    id: str
    title: str
    category: str
    completed: bool = False
    completed_at: Optional[str] = None

class OnboardingMetrics(BaseModel):
    calls_made: int = 0
    meetings_scheduled: int = 0
    deals_in_pipeline: int = 0
    revenue_generated: float = 0.0

class OnboardingStatus(BaseModel):
    candidate_id: int
    candidate_name: str
    start_date: str
    checklist: List[OnboardingChecklistItem]
    metrics: OnboardingMetrics
    completion_percentage: int
    days_since_start: int
    status: str  # onboarding, probation, completed, terminated

# Хранилище онбординга (в реальности - БД)
onboarding_storage: Dict[int, dict] = {}

@app.post("/v1/onboarding/{candidate_id}/start", response_model=OnboardingStatus, tags=["Onboarding"])
async def start_onboarding(candidate_id: int, start_date: str, db: AsyncSession = Depends(get_db)):
    """Stage 14: Начать онбординг для нанятого кандидата."""
    result = await db.execute(
        select(models.Candidate).where(models.Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    checklist = [
        OnboardingChecklistItem(id=item["id"], title=item["title"], category=item["category"])
        for item in ONBOARDING_CHECKLIST_TEMPLATE
    ]

    onboarding = {
        "candidate_id": candidate_id,
        "candidate_name": candidate.name or "Неизвестно",
        "start_date": start_date,
        "checklist": [c.model_dump() for c in checklist],
        "metrics": OnboardingMetrics().model_dump(),
        "status": "onboarding"
    }

    onboarding_storage[candidate_id] = onboarding

    return OnboardingStatus(
        candidate_id=candidate_id,
        candidate_name=candidate.name or "Неизвестно",
        start_date=start_date,
        checklist=checklist,
        metrics=OnboardingMetrics(),
        completion_percentage=0,
        days_since_start=0,
        status="onboarding"
    )

@app.get("/v1/onboarding/{candidate_id}", response_model=OnboardingStatus, tags=["Onboarding"])
def get_onboarding_status(candidate_id: int):
    """Получить статус онбординга."""
    if candidate_id not in onboarding_storage:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    data = onboarding_storage[candidate_id]
    checklist = [OnboardingChecklistItem(**item) for item in data["checklist"]]
    completed = sum(1 for item in checklist if item.completed)

    start = datetime.fromisoformat(data["start_date"])
    days = (datetime.utcnow() - start).days

    return OnboardingStatus(
        candidate_id=data["candidate_id"],
        candidate_name=data["candidate_name"],
        start_date=data["start_date"],
        checklist=checklist,
        metrics=OnboardingMetrics(**data["metrics"]),
        completion_percentage=int(completed / len(checklist) * 100),
        days_since_start=days,
        status=data["status"]
    )

@app.patch("/v1/onboarding/{candidate_id}/checklist/{item_id}", tags=["Onboarding"])
def update_checklist_item(candidate_id: int, item_id: str, completed: bool = True):
    """Отметить пункт чек-листа как выполненный."""
    if candidate_id not in onboarding_storage:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    for item in onboarding_storage[candidate_id]["checklist"]:
        if item["id"] == item_id:
            item["completed"] = completed
            item["completed_at"] = datetime.utcnow().isoformat() if completed else None
            return {"status": "updated"}

    raise HTTPException(status_code=404, detail="Checklist item not found")

@app.patch("/v1/onboarding/{candidate_id}/metrics", response_model=OnboardingMetrics, tags=["Onboarding"])
def update_onboarding_metrics(candidate_id: int, metrics: OnboardingMetrics):
    """Обновить метрики онбординга."""
    if candidate_id not in onboarding_storage:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    onboarding_storage[candidate_id]["metrics"] = metrics.model_dump()
    return metrics


# === Root Endpoint ===

@app.get("/")
def read_root():
    return {"message": "AI-HR Backend is running", "version": "0.3.0", "database": "connected"}
