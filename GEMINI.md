# GEMINI Onboarding for AI-HR Project

This document provides the essential context for the AI-HR project.

### WHY (Purpose)
To build an AI-powered recruitment funnel that automates candidate screening and predicts their success, saving time and improving hiring quality.

### WHAT (Functionality)
The project consists of two main components:
1.  **Backend (FastAPI):** An API that provides AI-powered screening services.
2.  **Frontend (Streamlit):** A simple web interface for demonstrating the backend's functionality.

### HOW (Architecture & Tech Stack)
- **Backend:**
    - **Location:** `src/backend/`
    - **Entrypoint:** `main.py`
    - **Stack:** Python, FastAPI, Pydantic, OpenAI API.
    - **API Endpoints:** Defined as decorated functions in `main.py`. Refer to the source code to see available paths and models.
    - **Dependencies:** Listed in `src/backend/requirements.txt`.
    - **Configuration:** Requires an `OPENAI_API_KEY`. See `src/backend/.env.example` for the required format.

- **Frontend:**
    - **Location:** `src/frontend/`
    - **Entrypoint:** `app.py`
    - **Stack:** Python, Streamlit, Requests.
    - **Dependencies:** Listed in `src/frontend/requirements.txt`.

### How to Run the Project
You must run two separate processes in two separate terminals.

**1. Run the Backend:**
```bash
# From the ai-hr directory
pip install -r src/backend/requirements.txt
uvicorn src.backend.main:app --reload
```

**2. Run the Frontend:**
```bash
# From the ai-hr directory
pip install -r src/frontend/requirements.txt
streamlit run src/frontend/app.py
```

### Code Style
- Follow standard PEP 8 conventions for Python.
- Use Pydantic for all API data models in the backend.
- Keep logic separated by function and endpoint.

---

## Parallel Work Protocol

This project is developed by multiple AI agents. Adherence to this protocol is mandatory to prevent conflicts.

**Source of Truth:** This `GEMINI.md` file, specifically the "Task Board" below, is the single source of truth for task management.

### Workflow

1.  **Sync:** Always run `git pull origin main` before starting any work.
2.  **Claim Task:**
    *   Choose a task from the "Task Board" with the status `Pending`.
    *   Update this file: put your name in `Assigned To` and change the status to `In Progress`.
    *   Commit and push this change immediately with the message `chore: [Your Name] started task "[Task Name]"`.
3.  **Develop:** Implement the feature. Minimize touching files outside the scope of your task.
4.  **Commit & Push Work:** When your feature is complete, commit your work using the format:
    ```
    feat: Short description of the feature
    
    Co-Authored-By: Agent Name <agent@email.com>
    ```
5.  **Update Task Board:** After pushing your feature, `pull` again. Then, update the task status to `Done` in this `GEMINI.md` file and push the change with the message `chore: [Your Name] completed task "[Task Name]"`.

---

## Task Board

| Task | Assigned To | Status | Notes |
|------|-------------|--------|-------|
| Stage 4: Motivation survey | Gemini | **Done** | Backend + Frontend готовы |
| Docker + docker-compose | Claude | **Done** | `docker/`, `docker-compose.yml` - working! |
| Stage 5: Cognitive test | Gemini | **Done** | Backend + Frontend готовы |
| Unit tests (pytest) | Claude | **Done** | 45 tests: Stage 2, 5, 7, 8, 12-14, CRUD Jobs/Candidates, Stats |
| Frontend: Stage 1 UI | Claude | **Done** | Восстановлено: форма + результат |
| Database Integration | Claude | **Done** | PostgreSQL + SQLAlchemy async, models.py, database.py |
| Stage 7: Personality Profile | Claude | **Done** | 14 вопросов, 7 шкал, sales_fit_score |
| Stage 8: Sales Block | Claude | **Done** | 8 ситуационных кейсов + AI-оценка |
| Stage 12: Interview Guide | Claude | **Done** | AI генерирует гайд для руководителя |
| Stage 13: Offer Management | Claude | **Done** | CRUD офферов со статусами |
| Stage 14: Onboarding | Claude | **Done** | Чек-лист + метрики |
| Stage 9-11 | | Skipped | Видео-интервью и тест-звонок - пока пропущены |

### Quick Start (Docker)
```bash
docker-compose up -d
# Backend:  http://localhost:8000/docs
# Frontend: http://localhost:8501
```

---

### Current API Endpoints

| Stage | Endpoint | Status |
|-------|----------|--------|
| 1. Job Generation | `POST /v1/jobs/generate` | Done |
| 2. Screening | `POST /v1/screen/stage2_screening` | Done |
| 3. Resume Scoring | `POST /v1/screen/stage3_resume_scoring` | Done |
| 4. Motivation Survey | `POST /v1/screen/stage4_motivation_survey` | Done |
| 5. Cognitive Test | `GET /v1/screen/stage5_cognitive_test/questions` | Done |
| 5. Cognitive Test | `POST /v1/screen/stage5_cognitive_test` | Done |
| 6. Behavioral Chat | `POST /v1/screen/stage6_behavioral_chat` | Done |
| 7. Personality Profile | `GET /v1/screen/stage7_personality/questions` | Done |
| 7. Personality Profile | `POST /v1/screen/stage7_personality` | Done |
| 8. Sales Block | `GET /v1/screen/stage8_sales/scenarios` | Done |
| 8. Sales Block | `POST /v1/screen/stage8_sales` | Done |
| 12. Interview Guide | `POST /v1/screen/stage12_interview_guide` | Done |
| 13. Offers | `POST/GET/PATCH /v1/offers` | Done |
| 14. Onboarding | `POST/GET/PATCH /v1/onboarding/{id}/*` | Done |
