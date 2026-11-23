from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.learning import Concept


@pytest.mark.asyncio
async def test_learning_session_lifecycle(client: AsyncClient):
    # 1. Register User
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "student1@institution.edu", "display_name": "Student One", "password": "Password123!"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Start learning session
    resp_start = await client.post(
        "/api/v1/learning-sessions",
        headers=headers,
        json={"concept_id": None, "mode": "learn"},
    )
    assert resp_start.status_code == 201
    session_data = resp_start.json()
    assert "id" in session_data
    session_id = session_data["id"]
    assert session_data["status"] == "active"
    assert len(session_data["sections"]) >= 1
    assert session_data["current_index"] == 0

    # 3. Retrieve session
    resp_get = await client.get(
        f"/api/v1/learning-sessions/{session_id}",
        headers=headers,
    )
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == session_id

    # 4. Update progress (mark section understood and advance)
    sec_id = session_data["sections"][0]["id"]
    resp_prog = await client.post(
        f"/api/v1/learning-sessions/{session_id}/progress",
        headers=headers,
        json={"current_index": 1, "understood_id": sec_id},
    )
    assert resp_prog.status_code == 200
    prog_data = resp_prog.json()
    assert prog_data["current_index"] == 1
    assert prog_data["sections"][0]["understood"] is True

    # 5. Complete session
    resp_comp = await client.post(
        f"/api/v1/learning/sessions/{session_id}/complete",
        headers=headers,
    )
    assert resp_comp.status_code == 200
    assert resp_comp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_quiz_and_mastery_pipeline(client: AsyncClient, db_session: AsyncSession):
    # 1. Register User
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "student2@institution.edu", "display_name": "Student Two", "password": "Password123!"},
    )
    assert reg.status_code == 201
    user_id = uuid.UUID(reg.json()["user"]["id"])
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed a Concept directly in DB for this user
    concept = Concept(
        user_id=user_id,
        canonical_name="Support Vector Machines",
        normalized_name="support vector machines",
        lemma="support vector machine",
        definition="Supervised learning models with associated learning algorithms that analyze data for classification.",
    )
    db_session.add(concept)
    await db_session.commit()
    await db_session.refresh(concept)
    concept_id = str(concept.id)

    # 3. Create Quiz Attempt
    resp_quiz = await client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={"concept_id": concept_id},
    )
    assert resp_quiz.status_code == 201
    quiz_data = resp_quiz.json()
    assert "attempt_id" in quiz_data
    attempt_id = quiz_data["attempt_id"]
    questions = quiz_data["questions"]
    assert len(questions) >= 1
    # Check that answers don't leak correct index to client
    assert "correct_index" not in questions[0]
    assert len(questions[0]["choices"]) == 4

    # 4. Get Quiz Attempt view
    resp_get_quiz = await client.get(
        f"/api/v1/quiz-attempts/{attempt_id}",
        headers=headers,
    )
    assert resp_get_quiz.status_code == 200
    assert resp_get_quiz.json()["attempt_id"] == attempt_id

    # 5. Submit Answers (answer index 0 for all questions)
    answers = [
        {"question_id": q["id"], "selected_index": 0}
        for q in questions
    ]
    resp_submit = await client.post(
        f"/api/v1/quiz-attempts/{attempt_id}/submit",
        headers=headers,
        json={"answers": answers},
    )
    assert resp_submit.status_code == 200
    res_data = resp_submit.json()
    assert "score_pct" in res_data
    assert "mastery_score" in res_data
    assert "mastery_delta" in res_data
    assert res_data["score_pct"] == 100.0  # Since mock questions have index 0 as correct
    assert len(res_data["review"]) == len(questions)

    # 6. Verify Mastery Endpoint
    resp_mastery_list = await client.get("/api/v1/mastery", headers=headers)
    assert resp_mastery_list.status_code == 200
    m_items = resp_mastery_list.json()["items"]
    assert len(m_items) >= 1
    assert m_items[0]["concept_id"] == concept_id

    # Single concept mastery detail
    resp_m_single = await client.get(f"/api/v1/mastery/{concept_id}", headers=headers)
    assert resp_m_single.status_code == 200
    single_data = resp_m_single.json()
    assert single_data["concept_id"] == concept_id
    assert len(single_data["history"]) >= 1

    # 7. Verify Learning Path Endpoint
    resp_path = await client.get("/api/v1/learning-path", headers=headers)
    assert resp_path.status_code == 200
    assert "items" in resp_path.json()

    # 8. Verify Dashboard Endpoints
    resp_dash = await client.get("/api/v1/dashboard", headers=headers)
    assert resp_dash.status_code == 200
    d_data = resp_dash.json()
    assert "overall_mastery" in d_data
    assert "band_counts" in d_data
    assert "recommended" in d_data
    assert "growth" in d_data
    assert "activity" in d_data

    # Sub-dashboard endpoints
    resp_dash_prog = await client.get("/api/v1/dashboard/progress", headers=headers)
    assert resp_dash_prog.status_code == 200

    resp_dash_act = await client.get("/api/v1/dashboard/recent-activity", headers=headers)
    assert resp_dash_act.status_code == 200

    resp_dash_rec = await client.get("/api/v1/dashboard/recommendations", headers=headers)
    assert resp_dash_rec.status_code == 200
