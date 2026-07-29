from app.models.problem_model import Problem
from app.models.testcase_model import TestCase
from worker.worker import process_submission


def test_grading_accepted(client, db_session):
    client.post(
        "/auth/register",
        json={"email": "grade_user1@example.com", "password": "password123"},
    )
    token = client.post(
        "/auth/login",
        json={"email": "grade_user1@example.com", "password": "password123"},
    ).json()["access_token"]

    problem = Problem(title="Multiply", description="Multiply 2 numbers")
    db_session.add(problem)
    db_session.commit()
    db_session.refresh(problem)

    tc = TestCase(
        problem_id=problem.id, input_data="3 4", expected_output="12"
    )
    db_session.add(tc)
    db_session.commit()

    code = "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a * b)"
    res = client.post(
        "/submit",
        json={"problem_id": problem.id, "language": "python", "code": code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 202
    sub_id = res.json()["id"]

    process_submission(sub_id)

    poll_res = client.get(
        f"/submissions/{sub_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "Accepted"


def test_grading_wrong_answer(client, db_session):
    client.post(
        "/auth/register",
        json={"email": "grade_user2@example.com", "password": "password123"},
    )
    token = client.post(
        "/auth/login",
        json={"email": "grade_user2@example.com", "password": "password123"},
    ).json()["access_token"]

    problem = Problem(title="Multiply WRONG", description="Multiply 2 numbers")
    db_session.add(problem)
    db_session.commit()
    db_session.refresh(problem)

    tc = TestCase(
        problem_id=problem.id, input_data="3 4", expected_output="12"
    )
    db_session.add(tc)
    db_session.commit()

    code = "print(0)"
    res = client.post(
        "/submit",
        json={"problem_id": problem.id, "language": "python", "code": code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 202
    sub_id = res.json()["id"]

    process_submission(sub_id)

    poll_res = client.get(
        f"/submissions/{sub_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "Wrong Answer"


def test_grading_time_limit_exceeded(client, db_session):
    client.post(
        "/auth/register",
        json={"email": "grade_user3@example.com", "password": "password123"},
    )
    token = client.post(
        "/auth/login",
        json={"email": "grade_user3@example.com", "password": "password123"},
    ).json()["access_token"]

    problem = Problem(title="Timeout Problem", description="Times out")
    db_session.add(problem)
    db_session.commit()
    db_session.refresh(problem)

    tc = TestCase(
        problem_id=problem.id, input_data="1", expected_output="1"
    )
    db_session.add(tc)
    db_session.commit()

    code = "import time\ntime.sleep(10)"
    res = client.post(
        "/submit",
        json={"problem_id": problem.id, "language": "python", "code": code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 202
    sub_id = res.json()["id"]

    process_submission(sub_id)

    poll_res = client.get(
        f"/submissions/{sub_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "Time Limit Exceeded"
