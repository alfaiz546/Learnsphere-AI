from app.agents.tools.weakness_tool import analyze_weaknesses
from app.agents.tools.study_plan_tool import generate_study_plan
from app.agents.tools.progress_analyzer import analyze_progress
from app.agents.tool_registry import ToolRegistry
from app.models.user import User

def test_ai_tools_direct(client, db_session):
    # Register user
    reg = client.post("/api/auth/register", json={
        "email": "agent_student@example.com",
        "username": "agentstudent",
        "password": "Password123!"
    })
    user_id_str = reg.json()["data"]["user_id"]
    import uuid
    user_uuid = uuid.UUID(user_id_str)
    
    # Tool registry
    registry = ToolRegistry(db_session, user_uuid)
    schemas = registry.get_tool_schemas()
    assert len(schemas) >= 5
    
    # Weakness tool
    weakness_res = analyze_weaknesses(db_session, user_uuid, 30)
    assert "weak_topics" in weakness_res
    assert "summary" in weakness_res
    
    # Progress tool
    progress_res = analyze_progress(db_session, user_uuid)
    assert "progress_summary" in progress_res
    assert "weekly_xp" in progress_res
    
    # Study plan tool
    plan_res = generate_study_plan(
        db_session, user_uuid,
        goal="Master Python data structures and algorithms in 30 days",
        available_hours_per_day=1.5,
        duration_days=30,
        weak_topics=["Recursion", "Binary Search"]
    )
    assert "plan_id" in plan_res
    assert plan_res["duration_days"] == 30
    assert len(plan_res["plan_data"]["schedule"]) == 30

def test_ai_hint_endpoint(client, db_session):
    reg = client.post("/api/auth/register", json={
        "email": "hint_user@example.com",
        "username": "hintuser",
        "password": "Password123!"
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Request hint
    import uuid
    dummy_qid = str(uuid.uuid4())
    res = client.post("/api/ai/hint", json={
        "question_id": dummy_qid,
        "student_answer": "wrong guess"
    }, headers=headers)
    assert res.status_code == 200
    assert "hint" in res.json()["data"]
