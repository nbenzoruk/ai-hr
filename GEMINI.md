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
