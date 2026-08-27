import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.models import User, Teacher, Student

# Use an in-memory SQLite database with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    from app.core.security import get_password_hash
    test_user = User(
        email="teacher@guruyuktha.edu",
        hashed_password=get_password_hash("teacher123"),
        full_name="Md. Shahazadi Begum",
        role="TEACHER"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    teacher = Teacher(
        user_id=test_user.id,
        employee_code="EMP-TEST",
        department="English",
        designation="Lecturer in English",
        college_name="GDC Ramachandrapuram"
    )
    db.add(teacher)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Guru Yuktha API"
    assert data["version"] == "1.0.0"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_auth_login_success():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@guruyuktha.edu", "password": "teacher123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "teacher@guruyuktha.edu"
    assert data["user"]["role"] == "TEACHER"

def test_auth_login_invalid():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@guruyuktha.edu", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_auth_signup_teacher():
    signup_data = {
        "email": "teacher.new@guruyuktha.edu",
        "password": "securepassword123",
        "full_name": "Prof. Alan Turing",
        "role": "TEACHER",
        "department": "Computer Science",
        "designation": "Professor",
        "college_name": "Cambridge"
    }
    response = client.post("/api/v1/auth/signup", json=signup_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["full_name"] == "Prof. Alan Turing"
    assert data["user"]["role"] == "TEACHER"

    dup_res = client.post("/api/v1/auth/signup", json=signup_data)
    assert dup_res.status_code == 400

def test_auth_signup_learner():
    signup_data = {
        "email": "learner.rahul@student.edu",
        "password": "learnerpassword123",
        "full_name": "Rahul Verma",
        "role": "LEARNER",
        "course": "B.Sc Computer Science",
        "semester": "IV Sem",
        "college_name": "Government Degree College",
        "roll_number": "2026-CS-042"
    }
    response = client.post("/api/v1/auth/signup", json=signup_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "LEARNER"
    assert data["user"]["full_name"] == "Rahul Verma"

def test_auth_signup_invalid_role():
    signup_data = {
        "email": "hacker@evil.com",
        "password": "password123",
        "full_name": "Malicious User",
        "role": "SUPERADMIN"
    }
    response = client.post("/api/v1/auth/signup", json=signup_data)
    assert response.status_code == 400
    assert "Invalid account role" in response.json()["detail"]

def test_auth_me_teacher():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@guruyuktha.edu", "password": "teacher123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "TEACHER"
    assert data["user"]["email"] == "teacher@guruyuktha.edu"
    assert data["teacher"]["department"] == "English"

def test_auth_me_learner():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "learner.rahul@student.edu", "password": "learnerpassword123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "LEARNER"
    assert data["user"]["email"] == "learner.rahul@student.edu"
    assert data["learner"] is not None
    assert data["learner"]["learner_id"].startswith("STU-")
    assert data["learner"]["course"] == "B.Sc Computer Science"

def test_unauthenticated_protected_route():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_role_authorization_guards():
    from app.core.security import require_teacher, require_learner
    from fastapi import HTTPException
    
    # 1. Login as Teacher
    t_login = client.post("/api/v1/auth/login", json={"email": "teacher@guruyuktha.edu", "password": "teacher123"})
    t_token = t_login.json()["access_token"]
    
    # 2. Login as Learner
    l_login = client.post("/api/v1/auth/login", json={"email": "learner.rahul@student.edu", "password": "learnerpassword123"})
    l_token = l_login.json()["access_token"]
    
    # Verify Teacher passes require_teacher
    t_headers = {"Authorization": f"Bearer {t_token}"}
    me_t = client.get("/api/v1/auth/me", headers=t_headers)
    assert me_t.json()["role"] == "TEACHER"
    
    # Verify Learner passes require_learner
    l_headers = {"Authorization": f"Bearer {l_token}"}
    me_l = client.get("/api/v1/auth/me", headers=l_headers)
    assert me_l.json()["role"] == "LEARNER"
    
    # Test function level guard behavior directly
    from app.models.models import User
    teacher_user = User(id=1, email="t@g.edu", full_name="Teacher", role="TEACHER")
    learner_user = User(id=2, email="l@g.edu", full_name="Learner", role="LEARNER")
    
    # require_teacher accepts teacher, rejects learner
    assert require_teacher(teacher_user).role == "TEACHER"
    with pytest.raises(HTTPException) as exc_info:
        require_teacher(learner_user)
    assert exc_info.value.status_code == 403
    
    # require_learner accepts learner, rejects teacher
    assert require_learner(learner_user).role == "LEARNER"
    with pytest.raises(HTTPException) as exc_info:
        require_learner(teacher_user)
    assert exc_info.value.status_code == 403

def test_students_crud_flow():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@guruyuktha.edu", "password": "teacher123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a student
    student_data = {
        "name": "K. Sai Venkat",
        "roll_number": "2024-ENG-001",
        "course": "B.A. (HEP)",
        "semester": "II Sem",
        "department": "Arts & Humanities",
        "phone": "+91 9876543210"
    }
    create_res = client.post("/api/v1/students", json=student_data, headers=headers)
    assert create_res.status_code == 200
    created_student = create_res.json()
    student_id = created_student["id"]
    assert created_student["name"] == "K. Sai Venkat"

    # 2. Duplicate roll number should fail
    dup_res = client.post("/api/v1/students", json=student_data, headers=headers)
    assert dup_res.status_code == 400

    # 3. Get students list
    list_res = client.get("/api/v1/students", headers=headers)
    assert list_res.status_code == 200
    students_list = list_res.json()
    assert len(students_list) >= 1

    # 4. Get student profile
    prof_res = client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert prof_res.status_code == 200
    profile_data = prof_res.json()
    assert profile_data["name"] == "K. Sai Venkat"

    # 5. Create Seminar Activity for student
    seminar_data = {
        "student_id": student_id,
        "topic": "Shakespeare's Sonnets",
        "seminar_date": "2026-03-15",
        "presentation_mode": "OFFLINE",
        "marks_obtained": 9.5,
        "max_marks": 10.0,
        "remarks": "Excellent analysis and articulation"
    }
    sem_res = client.post("/api/v1/activities/seminar", json=seminar_data, headers=headers)
    assert sem_res.status_code == 200
    assert "Shakespeare's Sonnets" in sem_res.json()["title"]

    # 6. Check Dashboard Summary
    dash_res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200

def test_reports_endpoints():
    csv_res = client.get("/api/v1/reports/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "GuruYuktha_Export" in csv_res.headers["content-disposition"]
