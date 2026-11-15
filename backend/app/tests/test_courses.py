from app.database.init_db import _seed_all

def test_get_subjects(client, db_session):
    # Seed data if empty
    from app.models.subject import Subject
    if db_session.query(Subject).count() == 0:
        _seed_all(db_session)
    
    response = client.get("/api/subjects")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 4

def test_get_courses(client, db_session):
    response = client.get("/api/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1

def test_course_detail_and_enroll(client, db_session):
    # Register a student
    reg = client.post("/api/auth/register", json={
        "email": "course_student@example.com",
        "username": "coursestudent",
        "password": "Password123!"
    })
    token = reg.cookies.get("access_token") or reg.json().get("data", {}).get("access_token")
    csrf = reg.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf} if csrf else {"Authorization": f"Bearer {token}"}
    
    courses_res = client.get("/api/courses")
    first_course_id = courses_res.json()["data"][0]["id"]
    
    detail_res = client.get(f"/api/courses/{first_course_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert detail["id"] == first_course_id
    assert "modules" in detail
    
    enroll_res = client.post(f"/api/courses/{first_course_id}/enroll", headers=headers)
    assert enroll_res.status_code == 200
    assert enroll_res.json()["success"] is True
