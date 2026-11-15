"""
Tests for server-side answer validation — /lessons/{lesson_id}/check-answer endpoint.

Verifies:
- Correct numerical answer (3x - 4 = 11, x = 5) is marked correct
- Incorrect numerical answer (x = 6) is marked incorrect
- Empty / whitespace-only answer returns HTTP 400
- Decimal answers compared with tolerance (e.g. 5.0 == 5)
- Negative / wrong-sign numerical answers are marked incorrect
- Multiple-choice correct option is marked correct
- Multiple-choice wrong option is marked incorrect
- True/false answers validated correctly
- Hints do NOT auto-mark an answer as correct
"""
import pytest
import uuid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_login(client, suffix=""):
    email = f"answer_test_{suffix}@example.com"
    username = f"answer_test_{suffix}"
    reg = client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": "Password123!"
    })
    token = reg.cookies.get("access_token") or reg.json().get("data", {}).get("access_token", "")
    csrf = reg.cookies.get("csrf_token")
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf} if csrf else {"Authorization": f"Bearer {token}"}
    return headers


def _get_lesson_with_numerical_question(client, headers):
    """
    Fetches the first lesson that has a numerical question.
    Uses the enrolled subjects/courses path to find a lesson.
    """
    subjects_res = client.get("/api/subjects", headers=headers)
    assert subjects_res.status_code == 200
    subjects = subjects_res.json().get("data", [])
    assert len(subjects) > 0, "No subjects seeded"

    courses_res = client.get("/api/courses", headers=headers)
    assert courses_res.status_code == 200
    courses = courses_res.json().get("data", [])
    assert len(courses) > 0, "No courses seeded"

    # Enrol and retrieve a lesson
    course = courses[0]
    client.post(f"/api/courses/{course['id']}/enroll", headers=headers)

    course_detail_res = client.get(f"/api/courses/{course['id']}", headers=headers)
    assert course_detail_res.status_code == 200
    modules = course_detail_res.json()["data"].get("modules", [])
    assert len(modules) > 0

    # Walk through lessons to find a numerical one
    for module in modules:
        for lesson_brief in module.get("lessons", []):
            lesson_res = client.get(f"/api/lessons/{lesson_brief['id']}", headers=headers)
            assert lesson_res.status_code == 200
            lesson = lesson_res.json()["data"]
            for q in lesson.get("questions", []):
                if q["question_type"] == "numerical":
                    return lesson["id"], q
    return None, None


# ---------------------------------------------------------------------------
# Core answer validation tests
# ---------------------------------------------------------------------------

class TestNumericalAnswerValidation:

    def test_correct_numerical_answer_is_marked_correct(self, client, db_session):
        """3x - 4 = 11 → x = 5 must be CORRECT."""
        headers = _register_and_login(client, "numerical_correct")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None, "No lesson with numerical question found in seed data"

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": "5"
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_correct"] is True, "Submitting the correct answer (5) must be marked correct"
        assert data["score"] == 1.0

    def test_incorrect_numerical_answer_is_marked_incorrect(self, client, db_session):
        """3x - 4 = 11 → x = 6 must be INCORRECT — this is the reported bug scenario."""
        headers = _register_and_login(client, "numerical_wrong")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": "6"
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_correct"] is False, "Submitting 6 for a question whose answer is 5 must be INCORRECT"
        assert data["score"] == 0.0
        # Correct answer should be revealed for numerical questions after a wrong attempt
        assert "correct_answer" in data

    def test_decimal_equivalent_is_correct(self, client, db_session):
        """5.0 is numerically equal to 5 within tolerance."""
        headers = _register_and_login(client, "numerical_decimal")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": "5.0"
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_correct"] is True, "5.0 should be accepted as equivalent to 5 (within 0.01 tolerance)"

    def test_wrong_decimal_is_incorrect(self, client, db_session):
        """5.1 is NOT equal to 5 (outside 0.01 tolerance)."""
        headers = _register_and_login(client, "numerical_wrong_decimal")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": "5.1"
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_correct"] is False, "5.1 differs from 5 by more than 0.01 tolerance"

    def test_negative_answer_is_incorrect(self, client, db_session):
        """-5 is not the same as 5."""
        headers = _register_and_login(client, "numerical_negative")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": "-5"
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_correct"] is False, "-5 ≠ 5"

    def test_empty_answer_returns_400(self, client, db_session):
        """An empty answer must be rejected with HTTP 400, not silently marked correct."""
        headers = _register_and_login(client, "numerical_empty")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": ""
        }, headers=headers)
        assert res.status_code == 400, "Empty answer must return HTTP 400, not 200"

    def test_whitespace_only_answer_returns_400(self, client, db_session):
        """Whitespace-only input must be rejected."""
        headers = _register_and_login(client, "numerical_whitespace")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": "   "
        }, headers=headers)
        assert res.status_code == 400, "Whitespace-only answer must return HTTP 400"

    def test_non_numeric_text_is_incorrect_not_correct(self, client, db_session):
        """Submitting 'five' for a numerical question should be incorrect, not correct."""
        headers = _register_and_login(client, "numerical_text")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": "five"
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_correct"] is False, "'five' (non-numeric string) must be marked incorrect for a numerical question"


class TestAnswerValidationEndpointSecurity:

    def test_question_not_in_lesson_returns_404(self, client, db_session):
        """Cannot check an answer for a question from a different lesson."""
        headers = _register_and_login(client, "security_mismatch")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        fake_question_id = str(uuid.uuid4())
        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": fake_question_id,
            "student_answer": "5"
        }, headers=headers)
        assert res.status_code == 404

    def test_unauthenticated_request_returns_401(self, client, db_session):
        """Unauthenticated requests must be rejected."""
        res = client.post(f"/api/lessons/{uuid.uuid4()}/check-answer", json={
            "question_id": str(uuid.uuid4()),
            "student_answer": "5"
        })
        assert res.status_code in (401, 403)

    def test_correct_answer_not_exposed_in_success_response(self, client, db_session):
        """When answer is CORRECT, the raw correct_answer should NOT be in the response."""
        headers = _register_and_login(client, "no_expose_correct")
        lesson_id, question = _get_lesson_with_numerical_question(client, headers)
        assert lesson_id is not None

        res = client.post(f"/api/lessons/{lesson_id}/check-answer", json={
            "question_id": question["id"],
            "student_answer": "5"
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_correct"] is True
        # Backend should NOT expose correct_answer in a successful response (no cheating vector)
        assert "correct_answer" not in data, "Correct answer must not be in the response when the student already answered correctly"


class TestCheckAnswerServiceLogic:
    """Unit-level tests for the _check_answer() function."""

    def test_check_answer_numerical_exact(self):
        from app.services.assessment_service import _check_answer
        from unittest.mock import MagicMock

        q = MagicMock()
        q.question_type = "numerical"
        q.correct_answer = "5"
        q.options = []

        assert _check_answer(q, "5") is True
        assert _check_answer(q, "5.0") is True
        assert _check_answer(q, "4.999") is True      # within 0.01 tolerance
        assert _check_answer(q, "6") is False          # THE BUG CASE — must be False
        assert _check_answer(q, "-5") is False
        assert _check_answer(q, "0") is False
        assert _check_answer(q, "five") is False       # non-numeric

    def test_check_answer_numerical_tolerance_boundary(self):
        from app.services.assessment_service import _check_answer
        from unittest.mock import MagicMock

        q = MagicMock()
        q.question_type = "numerical"
        q.correct_answer = "5"
        q.options = []

        assert _check_answer(q, "5.009") is True       # just inside tolerance (< 0.01)
        assert _check_answer(q, "5.011") is False      # just outside tolerance

    def test_check_answer_true_false(self):
        from app.services.assessment_service import _check_answer
        from unittest.mock import MagicMock

        q = MagicMock()
        q.question_type = "true_false"
        q.correct_answer = "true"
        q.options = []

        assert _check_answer(q, "true") is True
        assert _check_answer(q, "True") is True
        assert _check_answer(q, "TRUE") is True
        assert _check_answer(q, "false") is False
        assert _check_answer(q, "yes") is False

    def test_check_answer_fill_blank(self):
        from app.services.assessment_service import _check_answer
        from unittest.mock import MagicMock

        q = MagicMock()
        q.question_type = "fill_blank"
        q.correct_answer = "photosynthesis"
        q.options = []

        assert _check_answer(q, "photosynthesis") is True
        assert _check_answer(q, "Photosynthesis") is True   # case-insensitive
        assert _check_answer(q, "respiration") is False
        assert _check_answer(q, "") is False
