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

def test_auth_login_invalid():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@guruyuktha.edu", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_auth_signup_and_duplicate():
    signup_data = {
        "email": "newprof@guruyuktha.edu",
        "password": "securepassword123",
        "full_name": "Prof. Alan Turing",
        "department": "Computer Science",
        "designation": "Professor",
        "college_name": "Cambridge"
    }
    response = client.post("/api/v1/auth/signup", json=signup_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["full_name"] == "Prof. Alan Turing"

    dup_res = client.post("/api/v1/auth/signup", json=signup_data)
    assert dup_res.status_code == 400

def test_teacher_profile_me():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@guruyuktha.edu", "password": "teacher123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "English"
    assert data["college_name"] == "GDC Ramachandrapuram"

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
