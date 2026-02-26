"""
Tests for the Mergington High School Activities API
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def restore_activities():
    """Restore the activities dict to its original state after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9


def test_get_activities_structure():
    response = client.get("/activities")
    data = response.json()
    for name, details in data.items():
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)


def test_get_activities_contains_expected_clubs():
    response = client.get("/activities")
    data = response.json()
    expected = {"Chess Club", "Programming Class", "Gym Class", "Soccer Team",
                "Basketball Club", "Drama Club", "Art Workshop", "Math Olympiad",
                "Science Club"}
    assert expected == set(data.keys())


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "newstudent@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]


def test_signup_adds_participant():
    email = "newstudent@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert email in participants


def test_signup_activity_not_found():
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_already_registered():
    # michael is already in Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


def test_signup_url_encoded_activity_name():
    response = client.post(
        "/activities/Programming%20Class/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

def test_unregister_success():
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "michael@mergington.edu" in data["message"]


def test_unregister_removes_participant():
    email = "michael@mergington.edu"
    client.delete("/activities/Chess Club/unregister", params={"email": email})
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert email not in participants


def test_unregister_activity_not_found():
    response = client.delete(
        "/activities/Nonexistent Activity/unregister",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unregister_participant_not_signed_up():
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "nobody@mergington.edu"}
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"].lower()


def test_signup_then_unregister():
    email = "roundtrip@mergington.edu"
    client.post("/activities/Drama Club/signup", params={"email": email})

    participants_after_signup = client.get("/activities").json()["Drama Club"]["participants"]
    assert email in participants_after_signup

    client.delete("/activities/Drama Club/unregister", params={"email": email})

    participants_after_unregister = client.get("/activities").json()["Drama Club"]["participants"]
    assert email not in participants_after_unregister
