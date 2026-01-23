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
        prompt = FINAL_ASSESSMENT_PROMPT.format(chat_history_str=chat_history_str)
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
