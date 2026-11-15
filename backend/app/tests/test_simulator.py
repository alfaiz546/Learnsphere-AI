def test_simulator_endpoints(client, db_session):
    # Register student
    reg = client.post("/api/auth/register", json={
        "email": "simulator_tester@example.com",
        "username": "tester_sim",
        "password": "Password123!"
    })
    token = reg.cookies.get("access_token") or reg.json().get("data", {}).get("access_token")
    csrf = reg.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf} if csrf else {"Authorization": f"Bearer {token}"}

    # 1. Test benchmarks endpoint
    bench_res = client.get("/api/simulator/benchmarks")
    assert bench_res.status_code == 200
    bench_data = bench_res.json()["data"]
    assert bench_data["total_programs"] > 0
    assert len(bench_data["colleges"]) > 0
    assert "supported_exam_branches" in bench_data

    # 2. Test JEE Main + Computer Science (Valid Engineering combination)
    sim_res = client.post("/api/simulator/predict-admission", json={
        "target_exam": "JEE Main",
        "current_score_or_pct": 88.0,
        "category": "General",
        "branch_preference": "Computer Science & Engineering"
    }, headers=headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()["data"]
    assert "predicted_outcome" in sim_data
    assert sim_data["predicted_outcome"]["predicted_percentile"] > 98.0
    assert "admission_standing" in sim_data["predicted_outcome"]
    assert "predicted_rank" not in sim_data["predicted_outcome"]
    assert "rank_range" not in sim_data["predicted_outcome"]
    assert "estimated_rank" not in sim_data["metrics_breakdown"]
    assert "rank_range" not in sim_data["metrics_breakdown"]
    assert sim_data["metrics_breakdown"]["eligible_programs_count"] > 0
    assert "admission_outlook" in sim_data["metrics_breakdown"]
    assert "categorized_colleges" in sim_data
    # Verify categorized colleges exist and rank is not exposed in college cards
    total_colleges = len(sim_data["categorized_colleges"]["safe"]) + len(sim_data["categorized_colleges"]["target"]) + len(sim_data["categorized_colleges"]["reach"])
    assert total_colleges > 0
    if sim_data["categorized_colleges"]["safe"]:
        safe_card = sim_data["categorized_colleges"]["safe"][0]
        assert "closing_rank_historical" not in safe_card
        assert "cutoff_comparison" in safe_card

def test_neet_mbbs_prediction(client, db_session):
    # Register student
    reg = client.post("/api/auth/register", json={
        "email": "neet_tester@example.com",
        "username": "neet_student",
        "password": "Password123!"
    })
    token = reg.cookies.get("access_token") or reg.json().get("data", {}).get("access_token")
    csrf = reg.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf} if csrf else {"Authorization": f"Bearer {token}"}

    # Test NEET + MBBS
    sim_res = client.post("/api/simulator/predict-admission", json={
        "target_exam": "NEET",
        "current_score_or_pct": 88.0,
        "category": "General",
        "branch_preference": "MBBS"
    }, headers=headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()["data"]
    assert sim_data["simulation_inputs"]["target_exam"] == "NEET"
    assert sim_data["simulation_inputs"]["branch_preference"] == "MBBS"
    assert sim_data["predicted_outcome"]["predicted_percentile"] > 98.0

    # Ensure all returned colleges are Medical programs
    for tier in ["safe", "target", "reach"]:
        for college in sim_data["categorized_colleges"][tier]:
            assert college["branch"] == "MBBS"
            assert "NEET" in college["source"] or "MCC" in college["source"]

def test_incompatible_exam_and_branch_rejected(client, db_session):
    # Register student
    reg = client.post("/api/auth/register", json={
        "email": "incompatible_tester@example.com",
        "username": "tester_incomp",
        "password": "Password123!"
    })
    token = reg.cookies.get("access_token") or reg.json().get("data", {}).get("access_token")
    csrf = reg.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf} if csrf else {"Authorization": f"Bearer {token}"}

    # 1. Incompatible: NEET with Computer Science
    res1 = client.post("/api/simulator/predict-admission", json={
        "target_exam": "NEET",
        "current_score_or_pct": 85.0,
        "branch_preference": "Computer Science & Engineering"
    }, headers=headers)
    assert res1.status_code == 400
    assert "Incompatible combination" in res1.json()["detail"]
    assert "NEET" in res1.json()["detail"]

    # 2. Incompatible: JEE Main with MBBS
    res2 = client.post("/api/simulator/predict-admission", json={
        "target_exam": "JEE Main",
        "current_score_or_pct": 85.0,
        "branch_preference": "MBBS"
    }, headers=headers)
    assert res2.status_code == 400
    assert "Incompatible combination" in res2.json()["detail"]
    assert "JEE Main" in res2.json()["detail"]
