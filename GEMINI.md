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

## Multi-Agent Collaboration

This project is developed by multiple AI agents (Gemini, Claude, etc.) working in parallel.

### Important Git Behavior

**If you see changes in a file but `git status` shows "nothing to commit":**
- This means another agent already committed those changes
- Run `git log --oneline -5` to see recent commits
- Run `git pull` if you're behind remote

**Before making changes:**
```bash
git pull origin main  # Always sync first
git status            # Check for uncommitted changes
```

**Commit convention:**
```
feat: Short description

Co-Authored-By: Agent Name <noreply@anthropic.com>
```

### Current API Endpoints (as of latest commit)

| Stage | Endpoint | Status |
|-------|----------|--------|
| 1. Job Generation | `POST /v1/jobs/generate` | Done |
| 2. Screening | `POST /v1/screen/stage2_screening` | Done |
| 3. Resume Scoring | `POST /v1/screen/stage3_resume_scoring` | Done |
| 6. Behavioral Chat | `POST /v1/screen/stage6_behavioral_chat` | Done |

### Next Tasks (unclaimed)
- Stage 4: Motivation survey
- Stage 5: Cognitive test
- Stage 7-14: See `AI Sales Recruitment Funnel.xlsx`
- Docker + docker-compose
- Unit tests (pytest)
