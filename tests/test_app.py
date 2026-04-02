"""
Comprehensive test suite for Mergington High School API

Tests follow the AAA (Arrange-Act-Assert) pattern:
- ARRANGE: Set up test data and client
- ACT: Execute the action being tested
- ASSERT: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a TestClient instance for all tests"""
    return TestClient(app)


# ============================================================================
# GET / (Root endpoint - Redirect)
# ============================================================================

def test_root_redirects_to_index_html(client):
    """
    ARRANGE: Set up test client
    ACT: Make GET request to root endpoint
    ASSERT: Verify it redirects to /static/index.html with 307 status
    """
    # ARRANGE
    expected_url = "/static/index.html"
    
    # ACT
    response = client.get("/", follow_redirects=False)
    
    # ASSERT
    assert response.status_code == 307
    assert response.headers["location"] == expected_url


# ============================================================================
# GET /activities (List all activities)
# ============================================================================

def test_get_activities_returns_all_activities(client):
    """
    ARRANGE: Set up test client
    ACT: Make GET request to /activities endpoint
    ASSERT: Verify returns all 9 activities
    """
    # ARRANGE
    expected_activity_count = 9
    expected_activities = [
        "Chess Club", "Programming Class", "Gym Class",
        "Basketball Team", "Tennis Club", "Art Studio",
        "Drama Club", "Debate Team", "Science Club"
    ]
    
    # ACT
    response = client.get("/activities")
    activities = response.json()
    
    # ASSERT
    assert response.status_code == 200
    assert len(activities) == expected_activity_count
    for activity_name in expected_activities:
        assert activity_name in activities


def test_get_activities_returns_correct_fields(client):
    """
    ARRANGE: Set up test client and expected fields
    ACT: Make GET request to /activities endpoint
    ASSERT: Verify each activity has required fields
    """
    # ARRANGE
    required_fields = {"description", "schedule", "max_participants", "participants"}
    sample_activity = "Chess Club"
    
    # ACT
    response = client.get("/activities")
    activities = response.json()
    activity_data = activities[sample_activity]
    
    # ASSERT
    assert response.status_code == 200
    assert set(activity_data.keys()) == required_fields
    assert isinstance(activity_data["description"], str)
    assert isinstance(activity_data["schedule"], str)
    assert isinstance(activity_data["max_participants"], int)
    assert isinstance(activity_data["participants"], list)


# ============================================================================
# POST /activities/{activity_name}/signup (Signup endpoint)
# ============================================================================

def test_signup_valid_student(client):
    """
    ARRANGE: Set up test client, a valid activity, and a new email
    ACT: Make POST request to signup endpoint
    ASSERT: Verify response is successful and confirms signup message
    """
    # ARRANGE
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    
    # ACT
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # ASSERT
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity}"


def test_signup_duplicate_email_returns_400(client):
    """
    ARRANGE: Set up test client, valid activity, and an email already signed up
    ACT: Make POST request to signup with duplicate email
    ASSERT: Verify 400 status and appropriate error message
    """
    # ARRANGE
    activity = "Chess Club"
    email = "michael@mergington.edu"  # Already signed up
    
    # ACT
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # ASSERT
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_nonexistent_activity_returns_404(client):
    """
    ARRANGE: Set up test client, non-existent activity, and valid email
    ACT: Make POST request with non-existent activity
    ASSERT: Verify 404 status and appropriate error message
    """
    # ARRANGE
    activity = "Nonexistent Activity"
    email = "student@mergington.edu"
    
    # ACT
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # ASSERT
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_missing_email_parameter_returns_422(client):
    """
    ARRANGE: Set up test client with valid activity but no email
    ACT: Make POST request without email parameter
    ASSERT: Verify 422 status for validation error
    """
    # ARRANGE
    activity = "Chess Club"
    
    # ACT
    response = client.post(f"/activities/{activity}/signup")
    
    # ASSERT
    assert response.status_code == 422


def test_signup_updates_participants_list(client):
    """
    ARRANGE: Set up test client with a new email and get initial participant count
    ACT: Make POST request to signup and then get activity details
    ASSERT: Verify the new email is in the participants list
    """
    # ARRANGE
    activity = "Programming Class"
    email = "newprogrammer@mergington.edu"
    
    # Get initial participants
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity]["participants"])
    
    # ACT
    signup_response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Verify updated state
    updated_response = client.get("/activities")
    updated_participants = updated_response.json()[activity]["participants"]
    
    # ASSERT
    assert signup_response.status_code == 200
    assert email in updated_participants
    assert len(updated_participants) == initial_count + 1


# ============================================================================
# DELETE /activities/{activity_name}/participants (Unregister endpoint)
# ============================================================================

def test_unregister_removes_student(client):
    """
    ARRANGE: Set up test client with an enrolled student
    ACT: Make DELETE request to unregister endpoint
    ASSERT: Verify response is successful and confirms unregister message
    """
    # ARRANGE
    activity = "Chess Club"
    email = "michael@mergington.edu"  # Already signed up
    
    # ACT
    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email}
    )
    
    # ASSERT
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity}"


def test_unregister_nonexistent_activity_returns_404(client):
    """
    ARRANGE: Set up test client with non-existent activity
    ACT: Make DELETE request for non-existent activity
    ASSERT: Verify 404 status and appropriate error message
    """
    # ARRANGE
    activity = "Nonexistent Activity"
    email = "student@mergington.edu"
    
    # ACT
    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email}
    )
    
    # ASSERT
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unregister_student_not_enrolled_returns_400(client):
    """
    ARRANGE: Set up test client with student not enrolled in activity
    ACT: Make DELETE request for non-enrolled student
    ASSERT: Verify 400 status and appropriate error message
    """
    # ARRANGE
    activity = "Chess Club"
    email = "notastudentthere@mergington.edu"  # Not signed up
    
    # ACT
    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email}
    )
    
    # ASSERT
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"].lower()


def test_unregister_missing_email_parameter_returns_422(client):
    """
    ARRANGE: Set up test client with valid activity but no email
    ACT: Make DELETE request without email parameter
    ASSERT: Verify 422 status for validation error
    """
    # ARRANGE
    activity = "Chess Club"
    
    # ACT
    response = client.delete(f"/activities/{activity}/participants")
    
    # ASSERT
    assert response.status_code == 422


def test_unregister_after_signup_flow(client):
    """
    ARRANGE: Set up test client and sign up a student
    ACT: Sign up student, then unregister them
    ASSERT: Verify they are removed from participants list
    """
    # ARRANGE
    activity = "Drama Club"
    email = "dramaticstudent@mergington.edu"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity]["participants"])
    
    # ACT - Sign up
    signup_response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Get participant count after signup
    after_signup_response = client.get("/activities")
    after_signup_count = len(after_signup_response.json()[activity]["participants"])
    
    # Unregister
    unregister_response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email}
    )
    
    # Get final participant count
    final_response = client.get("/activities")
    final_participants = final_response.json()[activity]["participants"]
    
    # ASSERT
    assert signup_response.status_code == 200
    assert after_signup_count == initial_count + 1
    assert unregister_response.status_code == 200
    assert email not in final_participants
    assert len(final_participants) == initial_count
