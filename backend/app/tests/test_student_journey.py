import pytest
import uuid
from app.database.init_db import _seed_all
from app.models.question import Question

def test_complete_student_journey(client, db_session):
    """
    Validates Track 4, Option 2 end-to-end student journey:
    1. Register & Login
    2. Set Academic Profile (Class, Board, Marks, Target Exam, Career Goal, Category)
    3. Quick Skill Assessment (Diagnostic)
    4. Auto Strong & Weak Topic Analysis
    5. Study Plan Generation & Persistence
    6. College Admission & Exam Outcome Simulation
    7. AI Tutor Integration
    """
    if db_session.query(Question).count() < 10:
        _seed_all(db_session)

    # 1. Register & Login
    email = "hackathon_student@learnsphere.ai"
    reg = client.post("/api/auth/register", json={
        "email": email,
        "username": "hackathon_star",
        "password": "Password123!"
    })
    assert reg.status_code == 201
    token = reg.cookies.get("access_token") or reg.json().get("data", {}).get("access_token")
    csrf = reg.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf} if csrf else {"Authorization": f"Bearer {token}"}

    # 2. Update Student Academic Profile
    profile_payload = {
        "full_name": "Arjun Sharma",
        "current_class": "Grade 12",
        "board": "CBSE",
        "current_marks": 91.5,
        "target_exam": "JEE Main",
        "career_goal": "Computer Science & Engineering",
        "target_year": 2025,
        "category": "General",
        "daily_goal_minutes": 45
    }
    update_res = client.put("/api/student/profile", json=profile_payload, headers=headers)
    assert update_res.status_code == 200

    # Verify Profile Persistence
    get_prof = client.get("/api/student/profile", headers=headers)
    assert get_prof.status_code == 200
    prof_data = get_prof.json()["data"]["profile"]
    assert prof_data["current_class"] == "Grade 12"
    assert prof_data["board"] == "CBSE"
    assert prof_data["target_exam"] == "JEE Main"
    assert prof_data["career_goal"] == "Computer Science & Engineering"
    assert prof_data["category"] == "General"

    # 3. Quick Skill Diagnostic Assessment
    diag_res = client.get("/api/assessments/diagnostic", headers=headers)
    assert diag_res.status_code == 200
    diag_data = diag_res.json()["data"]
    assessment_id = diag_data["assessment_id"]
    questions = diag_data["questions"]
    assert len(questions) >= 5

    # 4. Submit Answers (answer some correctly, some intentionally wrong to create strong and weak topics)
    answers_to_submit = []
    for idx, q in enumerate(questions):
        # Even indices: answer with correct answer from DB
        # Odd indices: answer with dummy wrong answer
        db_q = db_session.query(Question).filter(Question.id == uuid.UUID(q["id"])).first()
        student_ans = db_q.correct_answer if (idx % 2 == 0 and db_q) else "wrong_answer_xyz"
        answers_to_submit.append({
            "question_id": q["id"],
            "student_answer": student_ans,
            "time_taken_seconds": 15
        })

    submit_res = client.post("/api/assessments/submit", json={
        "assessment_id": assessment_id,
        "answers": answers_to_submit
    }, headers=headers)
    assert submit_res.status_code == 200
    sub_data = submit_res.json()["data"]
    assert sub_data["total_questions"] == len(questions)
    assert sub_data["correct_answers"] > 0
    assert sub_data["xp_earned"] > 0

    # 5. Strong and Weak Topic Analysis
    topic_res = client.get("/api/progress/topic-analysis", headers=headers)
    assert topic_res.status_code == 200
    topic_data = topic_res.json()["data"]
    assert "strong_topics" in topic_data
    assert "weak_topics" in topic_data
    assert topic_data["total_evaluated_topics"] > 0

    # 6. Verify Dashboard reflection
    dash_res = client.get("/api/student/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert dash_data["stats"]["xp_total"] > 0
    assert len(dash_data["recent_results"]) >= 1

    # 7. Generate & Save Personalized Study Plan
    study_plan_res = client.post("/api/ai/study-plan", json={
        "goal": "Score 99+ percentile in JEE Main with focus on weak topics",
        "available_hours_per_day": 2.5,
        "duration_days": 7
    }, headers=headers)
    assert study_plan_res.status_code == 200
    plan_data = study_plan_res.json()["data"]
    assert "plan_id" in plan_data
    assert plan_data["duration_days"] == 7
    assert len(plan_data["plan_data"]["schedule"]) == 7

    # Verify Current Study Plan Loading
    current_plan_res = client.get("/api/ai/study-plan/current", headers=headers)
    assert current_plan_res.status_code == 200
    cur_plan_data = current_plan_res.json()["data"]
    assert cur_plan_data is not None
    assert cur_plan_data["plan_id"] == plan_data["plan_id"]

    # 8. College Admission & Exam Outcome Simulator
    sim_res = client.post("/api/simulator/predict-admission", json={
        "target_exam": "JEE Main",
        "current_score_or_pct": 91.5,
        "category": "General",
        "branch_preference": "Computer Science",
        "target_year": 2025
    }, headers=headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()["data"]
    assert sim_data["simulation_inputs"]["current_score_or_pct"] == 91.5
    assert sim_data["metrics_breakdown"]["mock_marks_percentage"] == 91.5
    assert sim_data["metrics_breakdown"]["predicted_percentile"] > 98.0
    assert sim_data["metrics_breakdown"]["eligible_programs_count"] > 0
    assert "estimated_rank" not in sim_data["metrics_breakdown"]
    assert "categorized_colleges" in sim_data
    assert len(sim_data["categorized_colleges"]["safe"]) + len(sim_data["categorized_colleges"]["target"]) + len(sim_data["categorized_colleges"]["reach"]) > 0
    assert "topic_impact" in sim_data

    # 9. AI Hint Endpoint
    hint_res = client.post("/api/ai/hint", json={
        "question_id": questions[0]["id"],
        "student_answer": "wrong_choice"
    }, headers=headers)
    assert hint_res.status_code == 200
    assert "hint" in hint_res.json()["data"]
