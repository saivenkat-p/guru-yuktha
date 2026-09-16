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

# =======================================================
# PHASE 2: ROOM CREATION + ROOM MEMBERSHIP TEST SUITE
# =======================================================

def test_room_creation_and_authorization():
    # 1. Teacher setup
    t_login = client.post("/api/v1/auth/login", json={"email": "teacher@guruyuktha.edu", "password": "teacher123"})
    t_token = t_login.json()["access_token"]
    t_headers = {"Authorization": f"Bearer {t_token}"}

    # 2. Ensure Learner is signed up
    l_login = client.post("/api/v1/auth/login", json={"email": "learner.rahul@student.edu", "password": "learnerpassword123"})
    if l_login.status_code != 200:
        l_signup = client.post("/api/v1/auth/signup", json={
            "email": "learner.rahul@student.edu",
            "password": "learnerpassword123",
            "full_name": "Rahul Verma",
            "role": "LEARNER",
            "course": "B.Sc Computer Science"
        })
        l_token = l_signup.json()["access_token"]
    else:
        l_token = l_login.json()["access_token"]
    l_headers = {"Authorization": f"Bearer {l_token}"}

    # Test 1: Teacher can create room
    room_payload = {
        "name": "Advanced British Literature",
        "description": "Exploration of 19th and 20th century poetry and drama.",
        "visibility": "PRIVATE"
    }
    create_res = client.post("/api/v1/rooms", json=room_payload, headers=t_headers)
    assert create_res.status_code == 201
    room_data = create_res.json()
    assert room_data["name"] == "Advanced British Literature"
    assert room_data["code"].startswith("ADV-") or "-" in room_data["code"]
    assert room_data["visibility"] == "PRIVATE"
    assert room_data["is_active"] is True
    assert room_data["active_members_count"] == 0
    room_id = room_data["id"]

    # Test 2: In Universal Member architecture, any Member can create room (Dual Context)
    l_create_res = client.post("/api/v1/rooms", json={"name": "Rahul's Study Group"}, headers=l_headers)
    assert l_create_res.status_code == 201
    assert l_create_res.json()["name"] == "Rahul's Study Group"

    # Test 3: Unauthenticated user cannot create room
    anon_res = client.post("/api/v1/rooms", json={"name": "Anon Room"})
    assert anon_res.status_code == 401

    # Test 4: Teacher can view own rooms list
    rooms_list = client.get("/api/v1/rooms", headers=t_headers)
    assert rooms_list.status_code == 200
    assert any(r["id"] == room_id for r in rooms_list.json())

    # Test 5: Teacher can view own room details
    room_det = client.get(f"/api/v1/rooms/{room_id}", headers=t_headers)
    assert room_det.status_code == 200
    assert room_det.json()["id"] == room_id

    # Test 6: Private room blocks unassociated learner
    l_view_res = client.get(f"/api/v1/rooms/{room_id}", headers=l_headers)
    assert l_view_res.status_code == 403

    # Test 7: Learner cannot modify teacher's room
    l_update_res = client.put(f"/api/v1/rooms/{room_id}", json={"name": "Tampered Name"}, headers=l_headers)
    assert l_update_res.status_code == 403

    # Test 8: Teacher 2 cannot modify Teacher 1's room
    # Register teacher 2
    t2_login = client.post("/api/v1/auth/login", json={"email": "teacher2.math@guruyuktha.edu", "password": "passWord123!"})
    if t2_login.status_code != 200:
        t2_signup = client.post("/api/v1/auth/signup", json={
            "email": "teacher2.math@guruyuktha.edu",
            "password": "passWord123!",
            "full_name": "Prof. Srinivasa Ramanujan",
            "role": "TEACHER",
            "department": "Mathematics",
            "designation": "Professor",
            "college_name": "GDC"
        })
        t2_token = t2_signup.json()["access_token"]
    else:
        t2_token = t2_login.json()["access_token"]
    t2_headers = {"Authorization": f"Bearer {t2_token}"}

    t2_update_res = client.put(f"/api/v1/rooms/{room_id}", json={"name": "Stolen Room"}, headers=t2_headers)
    assert t2_update_res.status_code == 403
    assert "You do not own this room" in t2_update_res.json()["detail"]

    # Test 9: Owning teacher CAN update room
    update_res = client.put(f"/api/v1/rooms/{room_id}", json={"name": "British Literature & Drama"}, headers=t_headers)
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "British Literature & Drama"

def test_room_membership_and_isolation():
    from app.models.models import Room, RoomMembership, User, Learner

    # Ensure teacher2 exists
    t2_login = client.post("/api/v1/auth/login", json={"email": "teacher2.math@guruyuktha.edu", "password": "passWord123!"})
    if t2_login.status_code != 200:
        client.post("/api/v1/auth/signup", json={
            "email": "teacher2.math@guruyuktha.edu",
            "password": "passWord123!",
            "full_name": "Prof. Srinivasa Ramanujan",
            "role": "TEACHER",
            "department": "Mathematics",
            "designation": "Professor",
            "college_name": "GDC"
        })

    # Ensure learner exists
    l_login = client.post("/api/v1/auth/login", json={"email": "learner.rahul@student.edu", "password": "learnerpassword123"})
    if l_login.status_code != 200:
        client.post("/api/v1/auth/signup", json={
            "email": "learner.rahul@student.edu",
            "password": "learnerpassword123",
            "full_name": "Rahul Verma",
            "role": "LEARNER",
            "course": "B.Sc Computer Science"
        })

    db = TestingSessionLocal()
    try:
        # Get users
        t1_user = db.query(User).filter(User.email == "teacher@guruyuktha.edu").first()
        t2_user = db.query(User).filter(User.email == "teacher2.math@guruyuktha.edu").first()
        learner_user = db.query(User).filter(User.email == "learner.rahul@student.edu").first()
        learner_profile = db.query(Learner).filter(Learner.user_id == learner_user.id).first()

        # Create Room 1 (Teacher 1)
        r1 = Room(
            teacher_id=t1_user.teacher_profile.id if t1_user.teacher_profile else None,
            owner_id=t1_user.id,
            name="English Honours 2026",
            code="ENG-HON-2026",
            visibility="PRIVATE",
            is_active=True
        )
        # Create Room 2 (Teacher 2)
        r2 = Room(
            teacher_id=t2_user.teacher_profile.id if t2_user.teacher_profile else None,
            owner_id=t2_user.id,
            name="Real Analysis 2026",
            code="MATH-REAL-2026",
            visibility="PUBLIC",
            is_active=True
        )
        db.add_all([r1, r2])
        db.commit()
        db.refresh(r1)
        db.refresh(r2)

        # Associate Learner with Room 1 and Room 2 (Learner can belong to multiple rooms)
        m1 = RoomMembership(
            room_id=r1.id,
            user_id=learner_user.id,
            learner_id=learner_profile.id if learner_profile else None,
            role="MEMBER",
            status="ACTIVE"
        )
        m2 = RoomMembership(
            room_id=r2.id,
            user_id=learner_user.id,
            learner_id=learner_profile.id if learner_profile else None,
            role="MEMBER",
            status="ACTIVE"
        )
        db.add_all([m1, m2])
        db.commit()

        # Login tokens
        t1_token = client.post("/api/v1/auth/login", json={"email": "teacher@guruyuktha.edu", "password": "teacher123"}).json()["access_token"]
        t2_token = client.post("/api/v1/auth/login", json={"email": "teacher2.math@guruyuktha.edu", "password": "passWord123!"}).json()["access_token"]
        l_token = client.post("/api/v1/auth/login", json={"email": "learner.rahul@student.edu", "password": "learnerpassword123"}).json()["access_token"]

        t1_headers = {"Authorization": f"Bearer {t1_token}"}
        t2_headers = {"Authorization": f"Bearer {t2_token}"}
        l_headers = {"Authorization": f"Bearer {l_token}"}

        # Test 10: Teacher 1 can see members of Room 1
        m_res1 = client.get(f"/api/v1/rooms/{r1.id}/members", headers=t1_headers)
        assert m_res1.status_code == 200
        assert len(m_res1.json()) == 1

        # Test 11: Teacher 2 cannot view members of Teacher 1's Room
        m_res2 = client.get(f"/api/v1/rooms/{r1.id}/members", headers=t2_headers)
        assert m_res2.status_code == 403

        # Test 12: Learner can view their own memberships across multiple rooms
        l_memberships = client.get("/api/v1/rooms/my/memberships", headers=l_headers)
        assert l_memberships.status_code == 200
        membership_room_ids = [m["room_id"] for m in l_memberships.json()]
        assert r1.id in membership_room_ids
        assert r2.id in membership_room_ids

        # Test 13: Public room is viewable by any authenticated user without creating membership
        # Register a 2nd learner who has NO membership
        l2_signup = client.post("/api/v1/auth/signup", json={
            "email": "learner2.untracked@student.edu",
            "password": "LearnerPass123!",
            "full_name": "Untracked Student",
            "role": "LEARNER"
        })
        l2_token = l2_signup.json()["access_token"]
        l2_headers = {"Authorization": f"Bearer {l2_token}"}

        # Public room r2 viewable by l2
        public_view = client.get(f"/api/v1/rooms/{r2.id}", headers=l2_headers)
        assert public_view.status_code == 200
        assert public_view.json()["visibility"] == "PUBLIC"

        # Check that viewing public room did NOT automatically create membership for l2
        l2_memberships = client.get("/api/v1/rooms/my/memberships", headers=l2_headers)
        assert l2_memberships.status_code == 200
        assert len(l2_memberships.json()) == 0  # Zero memberships created

        # Test 14: Teacher can archive room (soft deactivate)
        arch_res = client.delete(f"/api/v1/rooms/{r1.id}", headers=t1_headers)
        assert arch_res.status_code == 200
        assert arch_res.json()["message"] == "Room archived successfully"

        # Archived room is no longer in active rooms list
        active_rooms = client.get("/api/v1/rooms", headers=t1_headers).json()
        assert not any(r["id"] == r1.id for r in active_rooms)

    finally:
        db.close()

# =======================================================
# PHASE 3: FOLDERS + RESOURCES + PUBLIC DISCOVERY TESTS
# =======================================================

def test_phase3_folders_and_resources():
    # Login Teacher 1
    t1_token = client.post("/api/v1/auth/login", json={"email": "teacher@guruyuktha.edu", "password": "teacher123"}).json()["access_token"]
    t1_headers = {"Authorization": f"Bearer {t1_token}"}

    # Ensure Teacher 2
    t2_login = client.post("/api/v1/auth/login", json={"email": "teacher2.math@guruyuktha.edu", "password": "passWord123!"})
    if t2_login.status_code != 200:
        client.post("/api/v1/auth/signup", json={
            "email": "teacher2.math@guruyuktha.edu",
            "password": "passWord123!",
            "full_name": "Prof. Srinivasa Ramanujan",
            "role": "TEACHER"
        })
        t2_login = client.post("/api/v1/auth/login", json={"email": "teacher2.math@guruyuktha.edu", "password": "passWord123!"})
    t2_token = t2_login.json()["access_token"]
    t2_headers = {"Authorization": f"Bearer {t2_token}"}

    # Ensure Learner
    l_login = client.post("/api/v1/auth/login", json={"email": "learner.rahul@student.edu", "password": "learnerpassword123"})
    if l_login.status_code != 200:
        client.post("/api/v1/auth/signup", json={
            "email": "learner.rahul@student.edu",
            "password": "learnerpassword123",
            "full_name": "Rahul Verma",
            "role": "LEARNER"
        })
        l_login = client.post("/api/v1/auth/login", json={"email": "learner.rahul@student.edu", "password": "learnerpassword123"})
    l_token = l_login.json()["access_token"]
    l_headers = {"Authorization": f"Bearer {l_token}"}

    # 1. Create a Teacher 1 Room
    r_res = client.post("/api/v1/rooms", json={"name": "Literary Criticism 2026", "visibility": "PRIVATE"}, headers=t1_headers)
    assert r_res.status_code == 201
    room_id = r_res.json()["id"]

    # --- FOLDERS TESTS ---
    # 2. Teacher 1 creates Folder
    f_res = client.post(f"/api/v1/rooms/{room_id}/folders", json={"name": "Unit 1 — Aristotle Poetics"}, headers=t1_headers)
    assert f_res.status_code == 201
    folder_id = f_res.json()["id"]
    assert f_res.json()["name"] == "Unit 1 — Aristotle Poetics"

    # 3. List folders
    f_list = client.get(f"/api/v1/rooms/{room_id}/folders", headers=t1_headers)
    assert f_list.status_code == 200
    assert len(f_list.json()) >= 1

    # 4. Teacher 2 cannot modify Folder in Teacher 1's room (403)
    t2_f_edit = client.put(f"/api/v1/rooms/{room_id}/folders/{folder_id}", json={"name": "Hacked Folder"}, headers=t2_headers)
    assert t2_f_edit.status_code == 403

    # 5. Learner cannot modify Folder (403)
    l_f_edit = client.put(f"/api/v1/rooms/{room_id}/folders/{folder_id}", json={"name": "Learner Folder"}, headers=l_headers)
    assert l_f_edit.status_code == 403

    # --- RESOURCES TESTS ---
    # 6. Teacher 1 creates ROOM_ONLY Resource
    res_private_payload = {
        "title": "Aristotle Catharsis Lecture Notes",
        "description": "Comprehensive notes for midterm review.",
        "folder_id": folder_id,
        "resource_type": "PDF",
        "file_url": "https://storage.guruyuktha.edu/notes/poetics.pdf",
        "visibility": "ROOM_ONLY"
    }
    res_p = client.post(f"/api/v1/rooms/{room_id}/resources", json=res_private_payload, headers=t1_headers)
    assert res_p.status_code == 201
    res_private_id = res_p.json()["id"]
    assert res_p.json()["visibility"] == "ROOM_ONLY"
    assert res_p.json()["folder_name"] == "Unit 1 — Aristotle Poetics"

    # 7. Teacher 1 creates PUBLIC Resource
    res_public_payload = {
        "title": "Open Guide to Dramatic Theory",
        "description": "Public educational overview of classical dramatic structures.",
        "folder_id": folder_id,
        "resource_type": "PDF",
        "file_url": "https://storage.guruyuktha.edu/open/drama.pdf",
        "visibility": "PUBLIC"
    }
    res_pub = client.post(f"/api/v1/rooms/{room_id}/resources", json=res_public_payload, headers=t1_headers)
    assert res_pub.status_code == 201
    res_pub_id = res_pub.json()["id"]
    assert res_pub.json()["visibility"] == "PUBLIC"

    # 8. Invalid resource type rejected (400)
    bad_type_res = client.post(f"/api/v1/rooms/{room_id}/resources", json={
        "title": "Bad Resource",
        "resource_type": "EXE_MALWARE"
    }, headers=t1_headers)
    assert bad_type_res.status_code == 400

    # 9. Invalid visibility rejected (400)
    bad_vis_res = client.post(f"/api/v1/rooms/{room_id}/resources", json={
        "title": "Bad Visibility",
        "visibility": "SECRET_CLASSIFIED"
    }, headers=t1_headers)
    assert bad_vis_res.status_code == 400

    # 10. Teacher 2 cannot modify resource in Teacher 1's room (403)
    t2_res_edit = client.put(f"/api/v1/rooms/{room_id}/resources/{res_private_id}", json={"title": "Hacked Title"}, headers=t2_headers)
    assert t2_res_edit.status_code == 403

    # 11. Learner cannot modify resource (403)
    l_res_edit = client.put(f"/api/v1/rooms/{room_id}/resources/{res_private_id}", json={"title": "Learner Title"}, headers=l_headers)
    assert l_res_edit.status_code == 403

    # --- PUBLIC DISCOVERY & SEPARATION TESTS ---
    # 12. Public resource is discoverable via /api/v1/resources/public
    pub_disc = client.get("/api/v1/resources/public")
    assert pub_disc.status_code == 200
    pub_ids = [r["id"] for r in pub_disc.json()]
    assert res_pub_id in pub_ids
    assert res_private_id not in pub_ids  # Private resource is NOT in public discovery

    # 13. Viewing public resource does NOT create room membership or tracking
    initial_memberships = client.get("/api/v1/rooms/my/memberships", headers=l_headers).json()
    init_m_count = len(initial_memberships)

    # Learner accesses public resource detail
    pub_detail = client.get(f"/api/v1/rooms/{room_id}/resources/{res_pub_id}", headers=l_headers)
    assert pub_detail.status_code == 200
    assert pub_detail.json()["title"] == "Open Guide to Dramatic Theory"

    # Verify memberships count did NOT change
    after_memberships = client.get("/api/v1/rooms/my/memberships", headers=l_headers).json()
    assert len(after_memberships) == init_m_count

    # 14. Non-member learner is FORBIDDEN from viewing ROOM_ONLY resource (403)
    priv_detail_forbidden = client.get(f"/api/v1/rooms/{room_id}/resources/{res_private_id}", headers=l_headers)
    assert priv_detail_forbidden.status_code == 403

    # 15. Teacher archives resource
    arch_res = client.delete(f"/api/v1/rooms/{room_id}/resources/{res_pub_id}", headers=t1_headers)
    assert arch_res.status_code == 200

    # Archived resource is excluded from public discovery
    pub_disc_after = client.get("/api/v1/resources/public").json()
    assert not any(r["id"] == res_pub_id for r in pub_disc_after)

    # 16. Teacher archives folder
    arch_f = client.delete(f"/api/v1/rooms/{room_id}/folders/{folder_id}", headers=t1_headers)
    assert arch_f.status_code == 200
    f_list_after = client.get(f"/api/v1/rooms/{room_id}/folders", headers=t1_headers).json()
    assert not any(f["id"] == folder_id for f in f_list_after)

# =======================================================
# PHASE 4: TEACHER-DEFINED ACTIVITY ARCHITECTURE TESTS
# =======================================================

def test_phase4_teacher_defined_activities():
    # 1. Register Brand New Teacher A
    t_a_signup = client.post("/api/v1/auth/signup", json={
        "email": "teacher.alpha@guruyuktha.edu",
        "password": "AlphaPassword123!",
        "full_name": "Prof. Alpha",
        "role": "TEACHER"
    })
    assert t_a_signup.status_code == 200
    t_a_token = t_a_signup.json()["access_token"]
    t_a_headers = {"Authorization": f"Bearer {t_a_token}"}

    # 2. Register Brand New Teacher B
    t_b_signup = client.post("/api/v1/auth/signup", json={
        "email": "teacher.beta@guruyuktha.edu",
        "password": "BetaPassword123!",
        "full_name": "Prof. Beta",
        "role": "TEACHER"
    })
    assert t_b_signup.status_code == 200
    t_b_token = t_b_signup.json()["access_token"]
    t_b_headers = {"Authorization": f"Bearer {t_b_token}"}

    # Test 1: Brand new teacher A starts with ZERO activities
    t_a_acts = client.get("/api/v1/activities", headers=t_a_headers)
    assert t_a_acts.status_code == 200
    assert len(t_a_acts.json()) == 0

    # Test 2: Brand new teacher A dashboard summary returns 0 total students and 0 total activities
    t_a_summary = client.get("/api/v1/dashboard/summary", headers=t_a_headers)
    assert t_a_summary.status_code == 200
    s_data = t_a_summary.json()
    assert s_data["total_students"] == 0
    assert s_data["teacher_name"] == "Prof. Alpha"
    assert s_data["seminars_total"] == 0
    assert s_data["assignments_total"] == 0

    # Test 3: Teacher A creates a room
    r_a_res = client.post("/api/v1/rooms", json={"name": "Alpha Machine Learning"}, headers=t_a_headers)
    assert r_a_res.status_code == 201
    room_a_id = r_a_res.json()["id"]

    # Test 4: Teacher B creates a room
    r_b_res = client.post("/api/v1/rooms", json={"name": "Beta Quantum Physics"}, headers=t_b_headers)
    assert r_b_res.status_code == 201
    room_b_id = r_b_res.json()["id"]

    # Test 5: Teacher A creates custom activity with custom title and optional room
    act_a1 = client.post("/api/v1/activities", json={
        "title": "Unit 1 Assignment: Neural Network Backprop",
        "description": "Implement backpropagation in pure NumPy.",
        "room_id": room_a_id,
        "type": "ASSIGNMENT",
        "max_marks": 25.0,
        "due_date": "2026-09-15"
    }, headers=t_a_headers)
    assert act_a1.status_code == 201
    act_a1_data = act_a1.json()
    assert act_a1_data["title"] == "Unit 1 Assignment: Neural Network Backprop"
    assert act_a1_data["room_name"] == "Alpha Machine Learning"
    assert act_a1_data["max_marks"] == 25.0
    act_a1_id = act_a1_data["id"]

    # Test 6: Teacher A creates a custom named activity without room (general)
    act_a2 = client.post("/api/v1/activities", json={
        "title": "Group Seminar on Ethics in AI",
        "type": "SEMINAR",
        "max_marks": 10.0
    }, headers=t_a_headers)
    assert act_a2.status_code == 201
    assert act_a2.json()["title"] == "Group Seminar on Ethics in AI"

    # Test 7: Teacher A cannot attach activity to Teacher B's room (403)
    hack_room_res = client.post("/api/v1/activities", json={
        "title": "Hacked Activity in Room B",
        "room_id": room_b_id
    }, headers=t_a_headers)
    assert hack_room_res.status_code == 403

    # Test 8: Teacher B does NOT see Teacher A's activities (strict isolation)
    t_b_acts = client.get("/api/v1/activities", headers=t_b_headers)
    assert t_b_acts.status_code == 200
    assert len(t_b_acts.json()) == 0  # Teacher B still has 0 activities

    # Test 9: Teacher A sees their 2 activities
    t_a_acts_after = client.get("/api/v1/activities", headers=t_a_headers)
    assert t_a_acts_after.status_code == 200
    assert len(t_a_acts_after.json()) == 2

    # Test 10: Teacher B cannot modify Teacher A's activity (403)
    hack_edit = client.put(f"/api/v1/activities/{act_a1_id}", json={
        "title": "Maliciously Modified Title"
    }, headers=t_b_headers)
    assert hack_edit.status_code == 403

    # Test 11: Teacher B cannot delete Teacher A's activity (403)
    hack_del = client.delete(f"/api/v1/activities/{act_a1_id}", headers=t_b_headers)
    assert hack_del.status_code == 403

    # Test 12: Teacher A updates their own activity
    valid_edit = client.put(f"/api/v1/activities/{act_a1_id}", json={
        "title": "Unit 1 Assignment: Advanced Backprop & SGD",
        "max_marks": 30.0
    }, headers=t_a_headers)
    assert valid_edit.status_code == 200
    assert valid_edit.json()["title"] == "Unit 1 Assignment: Advanced Backprop & SGD"
    assert valid_edit.json()["max_marks"] == 30.0

    # Test 13: Legacy activity endpoints work and assign teacher ownership
    leg_res = client.post("/api/v1/activities/generic", json={
        "title": "Legacy Quiz 1",
        "date": "15/09/2026",
        "remarks": "Great participation"
    }, headers=t_a_headers)
    assert leg_res.status_code == 200
    assert leg_res.json()["title"] == "Legacy Quiz 1"

    # Test 14: Teacher A deletes their own activity
    del_res = client.delete(f"/api/v1/activities/{act_a1_id}", headers=t_a_headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Activity deleted successfully"

# =======================================================
# PHASE 5: UNIVERSAL MEMBER ARCHITECTURE COMPLETE SUITE
# =======================================================

def test_universal_member_architecture_complete():
    # 1. Universal Member Signup (No role specified, defaults to MEMBER)
    ravi_signup = client.post("/api/v1/auth/signup", json={
        "email": "ravi.teja@guruyuktha.org",
        "password": "Password123!",
        "full_name": "Ravi Teja",
        "bio": "Full-stack developer & Python enthusiast",
        "skills": "Python, React, FastAPI, System Design"
    })
    assert ravi_signup.status_code == 200
    ravi_data = ravi_signup.json()
    assert "access_token" in ravi_data
    ravi_user = ravi_data["user"]
    assert ravi_user["role"] == "MEMBER"
    assert ravi_user["guru_id"].startswith("GY-")
    assert len(ravi_user["guru_id"]) == 11  # "GY-" + 8 chars
    assert ravi_user["username"].startswith("ravi_teja")
    ravi_token = ravi_data["access_token"]
    ravi_headers = {"Authorization": f"Bearer {ravi_token}"}
    ravi_guru_id = ravi_user["guru_id"]
    ravi_username = ravi_user["username"]

    # 2. Universal Signin via email, username, and Guru ID
    for identifier in ["ravi.teja@guruyuktha.org", ravi_username, ravi_guru_id]:
        login_res = client.post("/api/v1/auth/login", json={
            "login": identifier,
            "password": "Password123!"
        })
        assert login_res.status_code == 200
        assert login_res.json()["user"]["guru_id"] == ravi_guru_id

    # 3. /me endpoint returns universal profile data
    me_res = client.get("/api/v1/auth/me", headers=ravi_headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["guru_id"] == ravi_guru_id
    assert me_data["user"]["username"] == ravi_username
    assert me_data["user"]["bio"] == "Full-stack developer & Python enthusiast"

    # 4. Signup second member (Ananya)
    ananya_signup = client.post("/api/v1/auth/signup", json={
        "email": "ananya.sharma@guruyuktha.org",
        "password": "Password123!",
        "full_name": "Ananya Sharma",
        "bio": "Data Scientist & AI Researcher"
    })
    assert ananya_signup.status_code == 200
    ananya_data = ananya_signup.json()
    ananya_token = ananya_data["access_token"]
    ananya_headers = {"Authorization": f"Bearer {ananya_token}"}
    ananya_username = ananya_data["user"]["username"]
    ananya_guru_id = ananya_data["user"]["guru_id"]

    # 5. Member Profile Lookup
    prof_by_uname = client.get(f"/api/v1/members/{ravi_username}")
    assert prof_by_uname.status_code == 200
    assert prof_by_uname.json()["guru_id"] == ravi_guru_id
    assert prof_by_uname.json()["full_name"] == "Ravi Teja"

    prof_by_gid = client.get(f"/api/v1/members/{ravi_guru_id}")
    assert prof_by_gid.status_code == 200
    assert prof_by_gid.json()["username"] == ravi_username

    # 6. Universal Follow / Shishya System
    # Ananya follows Ravi
    follow_res = client.post(f"/api/v1/members/{ravi_username}/follow", headers=ananya_headers)
    assert follow_res.status_code == 200
    assert follow_res.json()["is_following"] is True
    assert follow_res.json()["followers_count"] == 1

    # Check Ravi's followers list
    ravi_followers = client.get(f"/api/v1/members/{ravi_username}/followers")
    assert ravi_followers.status_code == 200
    assert any(f["username"] == ananya_username for f in ravi_followers.json())

    # Check Ananya's following list
    ananya_following = client.get(f"/api/v1/members/{ananya_username}/following")
    assert ananya_following.status_code == 200
    assert any(f["username"] == ravi_username for f in ananya_following.json())

    # Cannot follow self
    self_follow = client.post(f"/api/v1/members/{ravi_username}/follow", headers=ravi_headers)
    assert self_follow.status_code == 400

    # 7. Universal Search
    search_res = client.get("/api/v1/search?q=Ravi")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert any(g["guru_id"] == ravi_guru_id for g in search_data["members"])

    # Search by Guru ID directly
    gid_search = client.get(f"/api/v1/search?q={ravi_guru_id}")
    assert gid_search.status_code == 200
    assert any(g["guru_id"] == ravi_guru_id for g in gid_search.json()["members"])

    # 8. Dual Context: Room Creation by Member Ravi (Teaching context)
    room_res = client.post("/api/v1/rooms", json={
        "name": "Python Programming Masterclass",
        "description": "Comprehensive Python from basics to FastAPI microservices.",
        "visibility": "PRIVATE",
        "access_type": "PRIVATE_FREE"
    }, headers=ravi_headers)
    assert room_res.status_code == 201
    room_data = room_res.json()
    room_id = room_data["id"]
    assert room_data["access_type"] == "PRIVATE_FREE"
    assert room_data["owner_username"] == ravi_username

    # Ravi adds a folder and resources
    folder_res = client.post(f"/api/v1/rooms/{room_id}/folders", json={
        "name": "Module 1: Foundations"
    }, headers=ravi_headers)
    assert folder_res.status_code == 201
    folder_id = folder_res.json()["id"]

    # Resource 1: Preview allowed
    client.post(f"/api/v1/rooms/{room_id}/resources", json={
        "title": "Course Syllabus & Overview",
        "folder_id": folder_id,
        "resource_type": "PDF",
        "file_url": "https://cdn.guruyuktha.org/syllabus.pdf",
        "visibility": "ROOM_ONLY",
        "is_preview_allowed": True
    }, headers=ravi_headers)

    # Resource 2: Private (no preview)
    client.post(f"/api/v1/rooms/{room_id}/resources", json={
        "title": "Confidential Exam Paper",
        "folder_id": folder_id,
        "resource_type": "PDF",
        "file_url": "https://cdn.guruyuktha.org/secret-exam.pdf",
        "visibility": "ROOM_ONLY",
        "is_preview_allowed": False
    }, headers=ravi_headers)

    # 9. Safe Room Preview: Non-member Ananya previews Ravi's private room
    # Direct access to private room detail is blocked (403)
    blocked_detail = client.get(f"/api/v1/rooms/{room_id}", headers=ananya_headers)
    assert blocked_detail.status_code == 403

    # But Safe Preview is accessible (200) without revealing confidential file URLs!
    preview_res = client.get(f"/api/v1/rooms/{room_id}/preview")
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["name"] == "Python Programming Masterclass"
    assert preview_data["owner_username"] == ravi_username
    assert len(preview_data["folders"]) == 1
    # Check resources in preview:
    preview_resources = preview_data["preview_resources"]
    assert len(preview_resources) == 2
    # The preview-allowed resource has is_preview_allowed True
    allowed_r = next(r for r in preview_resources if r["title"] == "Course Syllabus & Overview")
    assert allowed_r["is_preview_allowed"] is True
    # The confidential resource has is_preview_allowed False
    secret_r = next(r for r in preview_resources if r["title"] == "Confidential Exam Paper")
    assert secret_r["is_preview_allowed"] is False

    # 10. Free Room Join Request Lifecycle
    # Ananya requests to join Ravi's room
    req_res = client.post(f"/api/v1/rooms/{room_id}/join-requests", headers=ananya_headers)
    assert req_res.status_code == 201
    join_req = req_res.json()
    req_id = join_req["id"]
    assert join_req["status"] == "PENDING"
    assert join_req["user_username"] == ananya_username

    # Duplicate request is rejected (400)
    dup_req = client.post(f"/api/v1/rooms/{room_id}/join-requests", headers=ananya_headers)
    assert dup_req.status_code == 400

    # Ravi views pending join requests
    requests_list = client.get(f"/api/v1/rooms/{room_id}/join-requests", headers=ravi_headers)
    assert requests_list.status_code == 200
    assert any(r["id"] == req_id for r in requests_list.json())

    # Ananya cannot view join requests (not owner -> 403)
    non_owner_view = client.get(f"/api/v1/rooms/{room_id}/join-requests", headers=ananya_headers)
    assert non_owner_view.status_code == 403

    # Ravi accepts Ananya's join request
    action_res = client.post(
        f"/api/v1/rooms/{room_id}/join-requests/{req_id}/action",
        json={"action": "ACCEPT"},
        headers=ravi_headers
    )
    assert action_res.status_code == 200
    assert action_res.json()["status"] == "ACTIVE"

    # Now Ananya CAN access the room details directly!
    ananya_room_detail = client.get(f"/api/v1/rooms/{room_id}", headers=ananya_headers)
    assert ananya_room_detail.status_code == 200
    assert ananya_room_detail.json()["name"] == "Python Programming Masterclass"

    # 11. Public Room Instant Join
    # Ananya creates a public room (Teaching context for Ananya)
    math_room = client.post("/api/v1/rooms", json={
        "name": "Advanced Mathematics & Calculus",
        "description": "Open study circle on calculus and linear algebra.",
        "visibility": "PUBLIC",
        "access_type": "PUBLIC_FREE"
    }, headers=ananya_headers).json()
    math_room_id = math_room["id"]

    # Ravi joins Ananya's public room instantly (Learning context for Ravi)
    ravi_join = client.post(f"/api/v1/rooms/{math_room_id}/join", headers=ravi_headers)
    assert ravi_join.status_code == 200
    assert ravi_join.json()["status"] == "ACTIVE"
    assert ravi_join.json()["role"] == "MEMBER"

    # Verify Ravi's Dual Context:
    # Ravi is OWNER in "Python Programming Masterclass"
    # Ravi is MEMBER in "Advanced Mathematics & Calculus"
    ravi_memberships = client.get("/api/v1/rooms/my/memberships", headers=ravi_headers).json()
    joined_room_ids = [m["room_id"] for m in ravi_memberships]
    assert math_room_id in joined_room_ids

