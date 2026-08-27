from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, get_current_user
from app.models.models import User, Teacher, Learner, UserRole
from app.schemas.schemas import (
    LoginRequest, SignUpRequest, Token, UserOut, TeacherOut, LearnerOut,
    TeacherProfileUpdate, LearnerProfileUpdate, AuthMeResponse
)

router = APIRouter()

@router.post("/signup", response_model=Token)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    role = (request.role or "TEACHER").upper().strip()
    if role not in (UserRole.TEACHER.value, UserRole.LEARNER.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account role. Allowed roles are 'TEACHER' and 'LEARNER'."
        )

    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please sign in instead."
        )
    
    new_user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if role == UserRole.TEACHER.value:
        teacher = Teacher(
            user_id=new_user.id,
            employee_code=request.employee_code or f"EMP-{new_user.id:04d}",
            department=request.department or "English",
            designation=request.designation or "Lecturer in English",
            college_name=request.college_name or "GDC Ramachandrapuram"
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
    elif role == UserRole.LEARNER.value:
        current_year = datetime.utcnow().year
        platform_id = f"STU-{current_year}-{new_user.id:06d}"
        learner = Learner(
            user_id=new_user.id,
            learner_id=platform_id,
            roll_number=request.roll_number,
            course=request.course,
            semester=request.semester,
            department=request.department,
            college_name=request.college_name,
            phone=request.phone
        )
        db.add(learner)
        db.commit()
        db.refresh(learner)

    access_token = create_access_token(subject=new_user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=AuthMeResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    learner = db.query(Learner).filter(Learner.user_id == current_user.id).first()

    # Legacy fallback for backward compatibility if teacher record wasn't populated
    if current_user.role == "TEACHER" and not teacher:
        teacher = Teacher(
            user_id=current_user.id,
            employee_code=f"EMP-{current_user.id:04d}",
            department="English",
            designation="Lecturer in English",
            college_name="GDC Ramachandrapuram"
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

    response_data = {
        "user": current_user,
        "role": current_user.role,
        "teacher": teacher,
        "learner": learner,
    }

    # Populate top-level fields for legacy consumers expecting TeacherOut directly
    if teacher:
        response_data.update({
            "id": teacher.id,
            "employee_code": teacher.employee_code,
            "department": teacher.department,
            "designation": teacher.designation,
            "college_name": teacher.college_name,
        })

    return response_data

@router.put("/profile", response_model=AuthMeResponse)
def update_profile(
    profile_in: TeacherProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = current_user
    if profile_in.full_name:
        user.full_name = profile_in.full_name
    if profile_in.email:
        user.email = profile_in.email
    if profile_in.avatar_url:
        user.avatar_url = profile_in.avatar_url
    db.commit()
    db.refresh(user)

    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if teacher:
        if profile_in.designation:
            teacher.designation = profile_in.designation
        if profile_in.department:
            teacher.department = profile_in.department
        if profile_in.college_name:
            teacher.college_name = profile_in.college_name
        if profile_in.employee_code:
            teacher.employee_code = profile_in.employee_code
        db.commit()
        db.refresh(teacher)

    learner = db.query(Learner).filter(Learner.user_id == current_user.id).first()
    if learner:
        if profile_in.department:
            learner.department = profile_in.department
        if profile_in.college_name:
            learner.college_name = profile_in.college_name
        db.commit()
        db.refresh(learner)

    return get_current_user_profile(current_user=user, db=db)

@router.post("/avatar", response_model=AuthMeResponse)
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"avatar_{current_user.id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    avatar_url = f"/uploads/avatar_{current_user.id}_{file.filename}"
    current_user.avatar_url = avatar_url

    db.commit()
    db.refresh(current_user)

    return get_current_user_profile(current_user=current_user, db=db)

