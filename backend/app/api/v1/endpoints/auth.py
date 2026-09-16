from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
import re
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, get_current_user
from app.models.models import User, Teacher, Learner, UserRole, Follow, Room, RoomMembership
from app.core.identity import generate_guru_id, generate_username
from app.schemas.schemas import (
    LoginRequest, SignUpRequest, Token, UserOut, TeacherOut, LearnerOut,
    TeacherProfileUpdate, LearnerProfileUpdate, AuthMeResponse
)

router = APIRouter()

def build_user_out(user: User, db: Session) -> UserOut:
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    rooms_owned_count = db.query(Room).filter(Room.owner_id == user.id, Room.is_active == True).count()
    rooms_joined_count = db.query(RoomMembership).filter(RoomMembership.user_id == user.id, RoomMembership.status == "ACTIVE").count()
    is_eligible = followers_count >= 100

    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role or "MEMBER",
        avatar_url=user.avatar_url,
        guru_id=user.guru_id,
        username=user.username,
        bio=user.bio,
        skills=user.skills,
        is_guru_eligible=is_eligible,
        followers_count=followers_count,
        following_count=following_count,
        rooms_owned_count=rooms_owned_count,
        rooms_joined_count=rooms_joined_count
    )

@router.post("/signup", response_model=Token)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    clean_email = request.email.lower().strip()
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please sign in instead."
        )

    raw_role = (request.role or "MEMBER").upper().strip()
    if raw_role not in ("TEACHER", "LEARNER", "STUDENT", "MEMBER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account role. Allowed roles are 'TEACHER', 'LEARNER', and 'MEMBER'."
        )
    assigned_role = raw_role if raw_role in ("TEACHER", "LEARNER") else "MEMBER"

    # Determine and validate unique username
    requested_username = (request.username or "").strip().lower().lstrip("@")
    if requested_username:
        if not re.match(r"^[a-z0-9_-]{3,30}$", requested_username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be 3-30 characters long and contain only letters, numbers, underscores, or hyphens."
            )
        if db.query(User).filter(User.username == requested_username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken. Please choose another username."
            )
        username = requested_username
    else:
        username = generate_username(request.full_name, clean_email, db=db)

    # Generate permanent, unique Guru ID
    guru_id = generate_guru_id(request.full_name, db=db)

    new_user = User(
        email=clean_email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name.strip(),
        role=assigned_role,
        guru_id=guru_id,
        username=username,
        bio=request.bio.strip() if request.bio else None,
        skills=request.skills.strip() if request.skills else None,
        is_guru_eligible=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Backward compatibility: populate legacy Teacher/Learner profiles if requested
    if assigned_role == "TEACHER" or request.designation or request.employee_code:
        teacher = Teacher(
            user_id=new_user.id,
            employee_code=request.employee_code or f"EMP-{new_user.id:04d}",
            department=request.department or "Academic",
            designation=request.designation or "Faculty",
            college_name=request.college_name or "Guru Yuktha Institution"
        )
        db.add(teacher)
        db.commit()

    if assigned_role == "LEARNER" or request.roll_number:
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

    access_token = create_access_token(subject=new_user.id)
    user_out = build_user_out(new_user, db)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_out
    }

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    login_id = (request.login or request.email or "").strip().lower()
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username is required"
        )

    user = db.query(User).filter(
        (User.email.ilike(login_id)) | 
        (User.username.ilike(login_id)) |
        (User.guru_id.ilike(login_id))
    ).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Ensure user has guru_id and username
    changed = False
    if not user.guru_id:
        user.guru_id = generate_guru_id(user.full_name, user.id, db)
        changed = True
    if not user.username:
        user.username = generate_username(user.full_name, user.email, user.id, db)
        changed = True
    if changed:
        db.commit()
        db.refresh(user)

    access_token = create_access_token(subject=user.id)
    user_out = build_user_out(user, db)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_out
    }

@router.get("/me", response_model=AuthMeResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Ensure user has guru_id and username
    changed = False
    if not current_user.guru_id:
        current_user.guru_id = generate_guru_id(current_user.full_name, current_user.id, db)
        changed = True
    if not current_user.username:
        current_user.username = generate_username(current_user.full_name, current_user.email, current_user.id, db)
        changed = True
    if changed:
        db.commit()
        db.refresh(current_user)

    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    learner = db.query(Learner).filter(Learner.user_id == current_user.id).first()

    user_out = build_user_out(current_user, db)

    response_data = {
        "user": user_out,
        "role": current_user.role or "MEMBER",
        "guru_id": current_user.guru_id,
        "username": current_user.username,
        "teacher": teacher,
        "learner": learner,
    }

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
        user.full_name = profile_in.full_name.strip()
    if profile_in.email:
        user.email = profile_in.email.strip().lower()
    if profile_in.avatar_url:
        user.avatar_url = profile_in.avatar_url
    if profile_in.bio is not None:
        user.bio = profile_in.bio.strip()
    if profile_in.skills is not None:
        user.skills = profile_in.skills.strip()
    if profile_in.username:
        clean_un = profile_in.username.strip().lower()
        if clean_un != user.username:
            existing = db.query(User).filter(User.username == clean_un).first()
            if existing:
                raise HTTPException(status_code=400, detail="Username is already taken.")
            user.username = clean_un
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

