from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List

# --- Configuration ---
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

app = FastAPI(
    title="AI-HR Assistant API",
    description="API for an AI-powered sales recruitment funnel.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "AI-HR Backend is running"}

@app.post("/v1/screen/stage2_screening", response_model=ScreeningResponse, tags=["Screening"])
def stage2_screening(request: ScreeningRequest):
    """
    Runs the initial screening (Stage 2) based on simple, non-negotiable criteria.

    This stage filters candidates on fundamental job requirements like willingness
    to make cold calls, desired work format, and salary expectations.
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
