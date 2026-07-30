from app.models.problem_model import Problem


def test_non_admin_cannot_create_problem(client):
    client.post(
        "/auth/register",
        json={"email": "stduser@example.com", "password": "password123"},
    )
    user_token = client.post(
        "/auth/login",
        json={"email": "stduser@example.com", "password": "password123"},
    ).json()["access_token"]

    res = client.post(
        "/problem",
        json={"title": "Unauthorized Problem", "description": "Desc"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert res.status_code == 403


def test_admin_can_create_problem(client):
    client.post(
        "/auth/register",
        json={
            "email": "adminuser@example.com",
            "password": "password123",
            "role": "admin",
        },
    )
    admin_token = client.post(
        "/auth/login",
        json={"email": "adminuser@example.com", "password": "password123"},
    ).json()["access_token"]

    res = client.post(
        "/problem",
        json={"title": "Admin Problem", "description": "Created by admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Admin Problem"
    assert data["created_by"] is not None


def test_submission_owner_isolation(client, db_session):
    problem = Problem(title="Iso Problem", description="Desc")
    db_session.add(problem)
    db_session.commit()
    db_session.refresh(problem)

    # Register Alice and Bob
    client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "password123"},
    )
    alice_token = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    ).json()["access_token"]
    bob_token = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "password123"},
    ).json()["access_token"]

    # Alice submits code
    sub_res = client.post(
        "/submit",
        json={"problem_id": problem.id, "language": "python", "code": "print('alice')"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert sub_res.status_code == 202
    sub_id = sub_res.json()["id"]

    # Alice views her submission -> 200
    alice_res = client.get(
        f"/submissions/{sub_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert alice_res.status_code == 200

    # Bob attempts to view Alice's submission -> 403 Forbidden
    bob_res = client.get(
        f"/submissions/{sub_id}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert bob_res.status_code == 403


def test_admin_can_view_any_submission(client, db_session):
    problem = Problem(title="Admin Access Problem", description="Desc")
    db_session.add(problem)
    db_session.commit()
    db_session.refresh(problem)

    # Register Charlie and Admin
    client.post(
        "/auth/register",
        json={"email": "charlie@example.com", "password": "password123"},
    )
    client.post(
        "/auth/register",
        json={
            "email": "sysadmin@example.com",
            "password": "password123",
            "role": "admin",
        },
    )
    charlie_token = client.post(
        "/auth/login",
        json={"email": "charlie@example.com", "password": "password123"},
    ).json()["access_token"]
    admin_token = client.post(
        "/auth/login",
        json={"email": "sysadmin@example.com", "password": "password123"},
    ).json()["access_token"]

    # Charlie submits code
    sub_res = client.post(
        "/submit",
        json={"problem_id": problem.id, "language": "python", "code": "print('charlie')"},
        headers={"Authorization": f"Bearer {charlie_token}"},
    )
    assert sub_res.status_code == 202
    sub_id = sub_res.json()["id"]

    # Admin views Charlie's submission -> 200 OK
    admin_res = client.get(
        f"/submissions/{sub_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["id"] == sub_id
