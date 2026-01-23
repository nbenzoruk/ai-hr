import os
import json
import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from dotenv import load_dotenv

# --- Environment and API Key Setup ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")
openai.api_key = OPENAI_API_KEY

# --- Application Setup ---
app = FastAPI(
    title="AI-HR Assistant API",
    description="API for an AI-powered sales recruitment funnel.",
    version="0.1.0"
)

# === STAGE 2: INITIAL SCREENING ===

# In a real app, this would come from a config file or database
SCREENING_QUESTIONS_CRITERIA = {
    "cold_calls": {"expected": True},
    "work_format": {"expected": "office"},
    "salary_expectation": {"max_allowed": 60000}
}

class ScreeningAnswer(BaseModel):
    question_id: str = Field(..., description="Identifier for the question, e.g., 'cold_calls'")
    answer: str | bool | int = Field(..., description="The candidate's answer")

class ScreeningRequest(BaseModel):
    answers: List[ScreeningAnswer]

class ScreeningResponse(BaseModel):
    passed: bool
    details: str

@app.post("/v1/screen/stage2_screening", response_model=ScreeningResponse, tags=["Screening"])
def stage2_screening(request: ScreeningRequest):
    """
    Runs the initial screening (Stage 2) based on simple, non-negotiable criteria.
    """
    candidate_answers = {ans.question_id: ans.answer for ans in request.answers}
    
    # Check willingness to make cold calls
    if candidate_answers.get("cold_calls") != SCREENING_QUESTIONS_CRITERIA["cold_calls"]["expected"]:
        return ScreeningResponse(passed=False, details="Candidate is not willing to make cold calls.")
        
    # Check work format preference
    if candidate_answers.get("work_format") != SCREENING_QUESTIONS_CRITERIA["work_format"]["expected"]:
        return ScreeningResponse(passed=False, details=f"Candidate prefers '{candidate_answers.get('work_format')}' format, but '{SCREENING_QUESTIONS_CRITERIA['work_format']['expected']}' is required.")

    # Check salary expectation
    salary_exp = candidate_answers.get("salary_expectation")
    if not isinstance(salary_exp, int) or salary_exp > SCREENING_QUESTIONS_CRITERIA["salary_expectation"]["max_allowed"]:
        return ScreeningResponse(
            passed=False, 
            details=f"Candidate's salary expectation ({salary_exp}) exceeds the maximum allowed ({SCREENING_QUESTIONS_CRITERIA['salary_expectation']['max_allowed']})."
        )

    return ScreeningResponse(passed=True, details="Candidate passed initial screening.")


# === STAGE 3: AI RESUME SCORING ===

RESUME_SCORING_PROMPT_TEMPLATE = """
You are an expert HR manager specializing in sales recruitment. Your task is to analyze a candidate's resume against a job description.

**Job Description:**
{job_description}

**Candidate's Resume:**
{resume_text}

**Your Analysis:**
Based on the provided texts, return a JSON object with the following structure:
{{
  "score": <An integer score from 0 to 100 representing how well the resume matches the job description. 100 is a perfect match.>,
  "summary": "<A 2-3 sentence summary of the candidate's strengths and weaknesses regarding this specific job.>",
  "red_flags": ["<A list of potential red flags or concerns, such as job hopping, lack of specific experience, or long career gaps. If no red flags, return an empty list.>"]
}}
"""

class ResumeScoringRequest(BaseModel):
    job_description: str
    resume_text: str

class ResumeScoringResponse(BaseModel):
    score: int = Field(..., description="Relevance score from 0 to 100.")
    summary: str = Field(..., description="AI's summary of the candidate's fit.")
    red_flags: List[str] = Field(..., description="Potential red flags.")

@app.post("/v1/screen/stage3_resume_scoring", response_model=ResumeScoringResponse, tags=["Screening"])
async def stage3_resume_scoring(request: ResumeScoringRequest):
    """
    Performs AI-powered resume screening (Stage 3).

    Compares the candidate's resume against the job description using an LLM
    to generate a score, a summary, and a list of potential red flags.
    """
    prompt = RESUME_SCORING_PROMPT_TEMPLATE.format(
        job_description=request.job_description,
        resume_text=request.resume_text
    )

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo", # Using a faster model for this task
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
Ты — опытный HR-директор, специализирующийся на подборе сейлз-менеджеров. Проанализируй следующий диалог с кандидатом.

**Диалог:**
{chat_history}

**Твоя задача:**
Оцени кандидата по 5-ти ключевым компетенциям для продаж:
1.  **Проактивность и нацеленность на результат:** Ищет ли решения, берет ли ответственность.
2.  **Честность и рефлексия:** Признает ли ошибки, делает ли выводы.
3.  **Стрессоустойчивость и работа с возражениями:** Как реагирует на неудачи и давление.
4.  **Структурность мышления:** Насколько логичны и последовательны его ответы.
5.  **Мотивация:** Что им движет (деньги, развитие, признание).

**Формат вывода:**
Верни ТОЛЬКО JSON-объект со следующей структурой:
{{
  "scores": {{
    "proactivity": <оценка от 0 до 100>,
    "honesty": <оценка от 0 до 100>,
    "resilience": <оценка от 0 до 100>,
    "structure": <оценка от 0 до 100>,
    "motivation": <оценка от 0 до 100>
  }},
  "final_summary": "<Краткое резюме на 3-4 предложения: сильные стороны, слабые стороны и общая рекомендация (рекомендую / рекомендую с осторожностью / не рекомендую).>",
  "is_complete": true
}}
"""

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class BehavioralChatRequest(BaseModel):
    conversation: List[ChatMessage] = Field(..., description="The entire conversation history so far.")

class BehavioralChatResponse(BaseModel):
    conversation: List[ChatMessage]
    assessment: dict | None = Field(None, description="The final assessment, only present at the end.")

@app.post("/v1/screen/stage6_behavioral_chat", response_model=BehavioralChatResponse, tags=["Screening"])
async def stage6_behavioral_chat(request: BehavioralChatRequest):
    """
    Conducts the behavioral assessment (Stage 6) via a simulated chat.

    This endpoint manages a conversation, asking a series of predefined behavioral
    questions. After the last question, it provides a final AI-powered assessment.
    """
    conversation = request.conversation
    user_message_count = sum(1 for msg in conversation if msg.role == 'user')

    if not conversation:
        # Start of the conversation
        next_question = BEHAVIORAL_QUESTIONS[0]
        conversation.append(ChatMessage(role="assistant", content=next_question))
        return BehavioralChatResponse(conversation=conversation)

    if user_message_count < len(BEHAVIORAL_QUESTIONS):
        # Continue the conversation
        next_question = BEHAVIORAL_QUESTIONS[user_message_count]
        conversation.append(ChatMessage(role="assistant", content=next_question))
        return BehavioralChatResponse(conversation=conversation)
    else:
        # End of the conversation, time for final assessment
        chat_history_str = "\n".join([f"{msg.role.capitalize()}: {msg.content}" for msg in conversation])
        prompt = FINAL_ASSESSMENT_PROMPT.format(chat_history_str=chat_history_str)

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.5,
            )
            assessment_json = response.choices[0].message.content
            assessment = json.loads(assessment_json)
            return BehavioralChatResponse(conversation=conversation, assessment=assessment)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get assessment from AI: {e}")

# === Root Endpoint ===

@app.get("/")
def read_root():
    return {"message": "AI-HR Backend is running"}
