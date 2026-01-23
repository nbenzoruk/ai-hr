import pytest
import pytest_asyncio
import json
from httpx import AsyncClient

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

async def test_read_root(async_client: AsyncClient):
    """Test the root endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI-HR Backend is running"
    assert "version" in data

# === Stage 2: Initial Screening Tests ===

@pytest.mark.parametrize("payload, expected_pass, expected_detail", [
    # Passing case - all criteria met
    ({
        "answers": [
            {"question_id": "cold_calls", "answer": True},
            {"question_id": "work_format", "answer": "office"},
            {"question_id": "salary_expectation", "answer": 55000}
        ]
    }, True, "Candidate passed initial screening."),
    # Passing case - exact max salary
    ({
        "answers": [
            {"question_id": "cold_calls", "answer": True},
            {"question_id": "work_format", "answer": "office"},
            {"question_id": "salary_expectation", "answer": 60000}
        ]
    }, True, "Candidate passed initial screening."),
    # Failure: not willing to make cold calls
    ({
        "answers": [
            {"question_id": "cold_calls", "answer": False},
            {"question_id": "work_format", "answer": "office"},
            {"question_id": "salary_expectation", "answer": 55000}
        ]
    }, False, "Candidate is not willing to make cold calls."),
    # Failure: prefers remote work
    ({
        "answers": [
            {"question_id": "cold_calls", "answer": True},
            {"question_id": "work_format", "answer": "remote"},
            {"question_id": "salary_expectation", "answer": 55000}
        ]
    }, False, "Candidate prefers 'remote' format, but 'office' is required."),
    # Failure: prefers hybrid work
    ({
        "answers": [
            {"question_id": "cold_calls", "answer": True},
            {"question_id": "work_format", "answer": "hybrid"},
            {"question_id": "salary_expectation", "answer": 55000}
        ]
    }, False, "Candidate prefers 'hybrid' format, but 'office' is required."),
    # Failure: salary expectation too high
    ({
        "answers": [
            {"question_id": "cold_calls", "answer": True},
            {"question_id": "work_format", "answer": "office"},
            {"question_id": "salary_expectation", "answer": 80000}
        ]
    }, False, "Candidate's salary expectation (80000) exceeds the maximum allowed (60000)."),
])
async def test_stage2_screening(async_client: AsyncClient, payload, expected_pass, expected_detail):
    """Test the Stage 2 screening endpoint with various scenarios."""
    response = await async_client.post("/v1/screen/stage2_screening", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["passed"] == expected_pass
    assert data["details"] == expected_detail

# === Stage 5: Cognitive Test Tests ===

async def test_get_cognitive_test_questions(async_client: AsyncClient):
    """Test the endpoint that serves cognitive test questions."""
    response = await async_client.get("/v1/screen/stage5_cognitive_test/questions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert "id" in data[0]
    assert "question" in data[0]
    assert "options" in data[0]

@pytest.mark.parametrize("answers, expected_score, expected_pass", [
    # Perfect score
    ([
        {"question_id": "logic_1", "answer": "Ложь"},
        {"question_id": "math_1", "answer": "5 рублей"},
        {"question_id": "attention_1", "answer": "11"}
    ], 3, True),
    # One mistake
    ([
        {"question_id": "logic_1", "answer": "Правда"},
        {"question_id": "math_1", "answer": "5 рублей"},
        {"question_id": "attention_1", "answer": "11"}
    ], 2, True),
    # Two mistakes
    ([
        {"question_id": "logic_1", "answer": "Правда"},
        {"question_id": "math_1", "answer": "10 рублей"},
        {"question_id": "attention_1", "answer": "11"}
    ], 1, False),
])
async def test_submit_cognitive_test(async_client: AsyncClient, answers, expected_score, expected_pass):
    """Test the cognitive test submission endpoint."""
    payload = {"answers": answers}
    response = await async_client.post("/v1/screen/stage5_cognitive_test", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == expected_score
    assert data["total"] == 3
    assert data["passed"] == expected_pass

# === AI Endpoint Tests with Mocking ===

@pytest_asyncio.fixture
def mock_ai_completion(monkeypatch):
    """Mocks the AI client's chat completion create method."""
    class MockChoice:
        def __init__(self, content):
            self.message = self.MockMessage(content)
        class MockMessage:
            def __init__(self, content):
                self.content = content
    class MockCompletions:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    async def mock_create(*args, **kwargs):
        # A simple mock that returns a predefined JSON structure
        # In a real scenario, this could be more sophisticated
        mock_response_content = {
            "job_title_final": "Mock Job Title",
            "job_description": "Mock description",
            "requirements": ["req1"],
            "nice_to_have": ["nice1"],
            "benefits": ["benefit1"],
            "screening_questions": [{"question": "q1", "type": "yes_no", "deal_breaker": False}],
            "salary_display": "100-200k",
            "tags": ["mock"],
            "score": 90,
            "summary": "Mock summary",
            "red_flags": [],
            "primary_motivation": "Деньги",
            "secondary_motivation": "Интерес к задачам",
            "analysis_summary": "Mock analysis",
            "scores": {},
            "final_summary": "Mock final summary",
            "is_complete": True
        }
        return MockCompletions(json.dumps(mock_response_content))

    monkeypatch.setattr("main.client.chat.completions.create", mock_create)

async def test_stage1_generate_job_posting_mocked(async_client: AsyncClient, mock_ai_completion):
    """Test Stage 1 (Job Generation) with a mocked AI response."""
    payload = {"job_title": "Test", "company_name": "Test", "sales_segment": "B2B", "salary_range": "100k"}
    response = await async_client.post("/v1/jobs/generate", json=payload)
    assert response.status_code == 200
    assert response.json()["job_title_final"] == "Mock Job Title"

async def test_stage3_resume_scoring_mocked(async_client: AsyncClient, mock_ai_completion):
    """Test Stage 3 (Resume Scoring) with a mocked AI response."""
    payload = {"job_description": "...", "resume_text": "..."}
    response = await async_client.post("/v1/screen/stage3_resume_scoring", json=payload)
    assert response.status_code == 200
    assert response.json()["score"] == 90

async def test_stage4_motivation_survey_mocked(async_client: AsyncClient, mock_ai_completion):
    """Test Stage 4 (Motivation Survey) with a mocked AI response."""
    payload = {"answer_motivation": "a", "answer_reason_for_leaving": "b", "answer_kpi": "c"}
    response = await async_client.post("/v1/screen/stage4_motivation_survey", json=payload)
    assert response.status_code == 200
    assert response.json()["primary_motivation"] == "Деньги"

async def test_stage6_behavioral_chat_final_assessment_mocked(async_client: AsyncClient, mock_ai_completion):
    """Test the final assessment part of Stage 6 (Behavioral Chat) with a mocked AI response."""
    # Simulate a conversation that is long enough to trigger the final assessment
    conversation = [{"role": "user", "content": "Response"}] * 5
    payload = {"conversation": conversation}
    response = await async_client.post("/v1/screen/stage6_behavioral_chat", json=payload)
    assert response.status_code == 200
    assert response.json()["assessment"]["final_summary"] == "Mock final summary"


# === CRUD Jobs Tests ===

# Test data fixtures
def sample_job_brief():
    return {
        "job_title": "Менеджер по продажам",
        "company_name": "ТестКомпания",
        "sales_segment": "B2B",
        "salary_range": "50000-80000",
        "work_format": "office"
    }

def sample_job_generated():
    return {
        "job_title_final": "Менеджер по продажам B2B",
        "job_description": "Описание вакансии для теста",
        "requirements": ["Опыт продаж от 1 года", "Коммуникабельность"],
        "nice_to_have": ["Знание CRM"],
        "benefits": ["ДМС", "Бонусы"],
        "screening_questions": [
            {"question": "Готовы ли вы делать холодные звонки?", "type": "yes_no", "deal_breaker": True}
        ],
        "salary_display": "от 50 000 до 80 000 руб.",
        "tags": ["B2B", "продажи"]
    }


async def test_create_job(async_client: AsyncClient):
    """Test creating a new job."""
    payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    response = await async_client.post("/v1/jobs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["job_title"] == "Менеджер по продажам"
    assert data["company_name"] == "ТестКомпания"
    assert data["job_title_final"] == "Менеджер по продажам B2B"
    assert data["is_active"] is True
    assert data["candidates_count"] == 0


async def test_list_jobs_empty(async_client: AsyncClient):
    """Test listing jobs when none exist."""
    response = await async_client.get("/v1/jobs")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_jobs(async_client: AsyncClient):
    """Test listing jobs after creating one."""
    # Create a job first
    payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    await async_client.post("/v1/jobs", json=payload)

    # List jobs
    response = await async_client.get("/v1/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == "Менеджер по продажам"


async def test_get_job_by_id(async_client: AsyncClient):
    """Test getting a job by ID."""
    # Create a job first
    payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    create_response = await async_client.post("/v1/jobs", json=payload)
    job_id = create_response.json()["id"]

    # Get job by ID
    response = await async_client.get(f"/v1/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["job_title"] == "Менеджер по продажам"


async def test_get_job_not_found(async_client: AsyncClient):
    """Test getting a non-existent job."""
    response = await async_client.get("/v1/jobs/99999")
    assert response.status_code == 404


# === CRUD Candidates Tests ===

async def test_create_candidate(async_client: AsyncClient):
    """Test creating a new candidate."""
    # Create a job first
    job_payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    job_response = await async_client.post("/v1/jobs", json=job_payload)
    job_id = job_response.json()["id"]

    # Create candidate
    candidate_payload = {
        "job_id": job_id,
        "name": "Иван Петров",
        "email": "ivan@test.com"
    }
    response = await async_client.post("/v1/candidates", json=candidate_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["job_id"] == job_id
    assert data["name"] == "Иван Петров"
    assert data["status"] == "in_progress"
    assert data["current_stage"] == "screening"


async def test_create_candidate_job_not_found(async_client: AsyncClient):
    """Test creating a candidate for non-existent job."""
    candidate_payload = {
        "job_id": 99999,
        "name": "Test User"
    }
    response = await async_client.post("/v1/candidates", json=candidate_payload)
    assert response.status_code == 404


async def test_list_candidates(async_client: AsyncClient):
    """Test listing candidates."""
    # Create job and candidate
    job_payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    job_response = await async_client.post("/v1/jobs", json=job_payload)
    job_id = job_response.json()["id"]

    candidate_payload = {"job_id": job_id, "name": "Тест Кандидат"}
    await async_client.post("/v1/candidates", json=candidate_payload)

    # List candidates
    response = await async_client.get("/v1/candidates")
    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["name"] == "Тест Кандидат"


async def test_list_candidates_filter_by_job(async_client: AsyncClient):
    """Test listing candidates filtered by job_id."""
    # Create two jobs
    job_payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    job1 = await async_client.post("/v1/jobs", json=job_payload)
    job1_id = job1.json()["id"]

    job_payload2 = {
        "brief": {**sample_job_brief(), "job_title": "Другая вакансия"},
        "generated": sample_job_generated()
    }
    job2 = await async_client.post("/v1/jobs", json=job_payload2)
    job2_id = job2.json()["id"]

    # Create candidates for different jobs
    await async_client.post("/v1/candidates", json={"job_id": job1_id, "name": "Кандидат 1"})
    await async_client.post("/v1/candidates", json={"job_id": job2_id, "name": "Кандидат 2"})

    # Filter by job_id
    response = await async_client.get(f"/v1/candidates?job_id={job1_id}")
    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["name"] == "Кандидат 1"


async def test_get_candidate_detail(async_client: AsyncClient):
    """Test getting detailed candidate info."""
    # Create job and candidate
    job_payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    job_response = await async_client.post("/v1/jobs", json=job_payload)
    job_id = job_response.json()["id"]

    candidate_payload = {"job_id": job_id, "name": "Детальный Кандидат"}
    create_response = await async_client.post("/v1/candidates", json=candidate_payload)
    candidate_id = create_response.json()["id"]

    # Get candidate detail
    response = await async_client.get(f"/v1/candidates/{candidate_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == candidate_id
    assert data["name"] == "Детальный Кандидат"


async def test_get_candidate_not_found(async_client: AsyncClient):
    """Test getting a non-existent candidate."""
    response = await async_client.get("/v1/candidates/99999")
    assert response.status_code == 404


async def test_update_candidate_stage_screening(async_client: AsyncClient):
    """Test updating candidate screening stage."""
    # Create job and candidate
    job_payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    job_response = await async_client.post("/v1/jobs", json=job_payload)
    job_id = job_response.json()["id"]

    candidate_payload = {"job_id": job_id, "name": "Обновляемый Кандидат"}
    create_response = await async_client.post("/v1/candidates", json=candidate_payload)
    candidate_id = create_response.json()["id"]

    # Update screening stage
    update_payload = {
        "stage": "screening",
        "data": {"cold_calls": True, "work_format": "office"},
        "passed": True
    }
    response = await async_client.patch(f"/v1/candidates/{candidate_id}/stage", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["screening_passed"] is True
    assert data["current_stage"] == "resume"


async def test_update_candidate_stage_rejection(async_client: AsyncClient):
    """Test candidate rejection during screening."""
    # Create job and candidate
    job_payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    job_response = await async_client.post("/v1/jobs", json=job_payload)
    job_id = job_response.json()["id"]

    candidate_payload = {"job_id": job_id, "name": "Отклоняемый Кандидат"}
    create_response = await async_client.post("/v1/candidates", json=candidate_payload)
    candidate_id = create_response.json()["id"]

    # Reject at screening stage
    update_payload = {
        "stage": "screening",
        "data": {"cold_calls": False},
        "passed": False
    }
    response = await async_client.patch(f"/v1/candidates/{candidate_id}/stage", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["screening_passed"] is False
    assert data["status"] == "rejected"
    assert data["current_stage"] == "screening"


# === Stats Endpoint Test ===

async def test_get_stats_empty(async_client: AsyncClient):
    """Test stats endpoint with no data."""
    response = await async_client.get("/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_jobs"] == 0
    assert data["active_jobs"] == 0
    assert data["total_candidates"] == 0


async def test_get_stats_with_data(async_client: AsyncClient):
    """Test stats endpoint with jobs and candidates."""
    # Create a job
    job_payload = {
        "brief": sample_job_brief(),
        "generated": sample_job_generated()
    }
    job_response = await async_client.post("/v1/jobs", json=job_payload)
    job_id = job_response.json()["id"]

    # Create candidates
    for i in range(3):
        await async_client.post("/v1/candidates", json={"job_id": job_id, "name": f"Кандидат {i}"})

    # Get stats
    response = await async_client.get("/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_jobs"] == 1
    assert data["active_jobs"] == 1
    assert data["total_candidates"] == 3
