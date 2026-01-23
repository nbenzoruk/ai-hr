import os
import json
from openai import AsyncOpenAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from dotenv import load_dotenv

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
app = FastAPI(
    title="AI-HR Assistant API",
    description="API for an AI-powered sales recruitment funnel.",
    version="0.1.0"
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
    job_title: str = Field(..., example="Менеджер по продажам B2B")
    company_name: str = Field(..., example="ТехноСофт")
    company_description: str | None = Field(None, example="IT-компания, разрабатывающая CRM-системы")
    sales_segment: str = Field(..., example="B2B SaaS, средний бизнес")
    salary_range: str = Field(..., example="80 000 - 150 000 руб + % от продаж")
    sales_target: str | None = Field(None, example="500 000 руб/мес выручки")
    work_format: str = Field(default="office", example="office / remote / hybrid")
    additional_requirements: str | None = Field(None, example="Опыт работы с CRM, английский язык")

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

    Принимает базовую информацию о позиции и генерирует:
    - Полный текст вакансии
    - Список требований и преимуществ
    - Скрининг-вопросы для первичного отбора
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
    answer: str | bool | int

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
    assessment: dict | None = None

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

# === Root Endpoint ===

@app.get("/")
def read_root():
    return {"message": "AI-HR Backend is running"}
