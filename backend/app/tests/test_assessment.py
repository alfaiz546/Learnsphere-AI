from app.database.init_db import _seed_all
from app.models.question import Question

def test_assessment_flow(client, db_session):
    if db_session.query(Question).count() == 0:
        _seed_all(db_session)
    
    # Register student
    reg = client.post("/api/auth/register", json={
        "email": "assessment_tester@example.com",
        "username": "tester_assess",
        "password": "Password123!"
    })
    token = reg.cookies.get("access_token") or reg.json().get("data", {}).get("access_token")
    csrf = reg.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf} if csrf else {"Authorization": f"Bearer {token}"}
    
    # Find a question
    q = db_session.query(Question).filter(Question.correct_answer != None).first()
    assert q is not None
    
    # Start assessment
    start_res = client.post("/api/assessments/start", json={"lesson_id": str(q.lesson_id)}, headers=headers)
    assert start_res.status_code == 201
    assessment_id = start_res.json()["data"]["assessment_id"]
    
    # Submit correct answer
    submit_res = client.post("/api/assessments/submit", json={
        "assessment_id": assessment_id,
        "answers": [
            {
                "question_id": str(q.id),
                "student_answer": q.correct_answer,
                "time_taken_seconds": 12
            }
        ]
    }, headers=headers)
    
    assert submit_res.status_code == 200
    res_data = submit_res.json()["data"]
    assert res_data["total_questions"] == 1
    assert res_data["correct_answers"] == 1
    assert res_data["score_percentage"] == 100.0
    assert res_data["xp_earned"] > 0
    
    # Check dashboard reflects results and XP
    dash_res = client.get("/api/student/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert dash_data["stats"]["xp_total"] > 0
    assert len(dash_data["recent_results"]) >= 1

def test_diagnostic_assessment(client, db_session):
    if db_session.query(Question).count() == 0:
        _seed_all(db_session)
    
    # Register student
    reg = client.post("/api/auth/register", json={
        "email": "diagnostic_tester@example.com",
        "username": "tester_diag",
        "password": "Password123!"
    })
    token = reg.cookies.get("access_token") or reg.json().get("data", {}).get("access_token")
    csrf = reg.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf} if csrf else {"Authorization": f"Bearer {token}"}
    
    # Request diagnostic assessment
    diag_res = client.get("/api/assessments/diagnostic", headers=headers)
    assert diag_res.status_code == 200
    diag_data = diag_res.json()["data"]
    assert "assessment_id" in diag_data
    assert diag_data["total_questions"] > 0
    assert len(diag_data["questions"]) > 0
    
    first_q = diag_data["questions"][0]
    assert "question_text" in first_q
    assert "subject_name" in first_q
    assert "tags" in first_q
    
    # Submit answer
    submit_res = client.post("/api/assessments/submit", json={
        "assessment_id": diag_data["assessment_id"],
        "answers": [
            {
                "question_id": first_q["id"],
                "student_answer": "test_answer",
                "time_taken_seconds": 10
            }
        ]
    }, headers=headers)
    assert submit_res.status_code == 200
