from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import require_teacher
from app.models.models import (
    Activity, SeminarDetail, AssignmentDetail, PblDetail, PglDetail, EvidenceFile,
    ActivityType, ActivityStatus, PresentationMode, ParticipationLevel, Student, User, Teacher, Room
)
from app.schemas.schemas import (
    ActivityOut, ActivityCreate, ActivityUpdate, SeminarCreate, AssignmentCreate, PblCreate, PglCreate, GenericActivityCreate
)

router = APIRouter()

def get_or_create_teacher(user: User, db: Session) -> Teacher:
    teacher = db.query(Teacher).filter(Teacher.user_id == user.id).first()
    if not teacher:
        teacher = Teacher(
            user_id=user.id,
            employee_code=f"EMP-{user.id:04d}",
            department="Academic",
            designation="Faculty",
            college_name="Institution"
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
    return teacher

def format_activity_out(act: Activity) -> ActivityOut:
    room_name = act.room.name if act.room else None
    room_code = act.room.code if act.room else None
    out = ActivityOut.model_validate(act)
    out.room_name = room_name
    out.room_code = room_code
    return out

# ================= PRIMARY TEACHER-DEFINED ACTIVITY ENDPOINTS =================

@router.get("", response_model=List[ActivityOut])
def get_activities(
    room_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    query = db.query(Activity).filter(Activity.teacher_id == teacher.id)

    if room_id:
        query = query.filter(Activity.room_id == room_id)
    if student_id:
        query = query.filter(Activity.student_id == student_id)
    if type and type.upper() != "ALL":
        query = query.filter(Activity.type == type.upper())

    activities = query.order_by(Activity.created_at.desc()).all()
    return [format_activity_out(a) for a in activities]

@router.post("", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
def create_activity(
    act_in: ActivityCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)

    # Validate room ownership if room_id is passed
    room = None
    if act_in.room_id:
        room = db.query(Room).filter(Room.id == act_in.room_id).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        if room.teacher_id != teacher.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You cannot attach activities to another teacher's room.")

    activity = Activity(
        teacher_id=teacher.id,
        room_id=act_in.room_id,
        student_id=act_in.student_id,
        type=(act_in.type or "ACTIVITY").upper(),
        title=act_in.title.strip(),
        description=act_in.description.strip() if act_in.description else None,
        status=ActivityStatus.IN_PROGRESS,
        max_marks=act_in.max_marks or 10.0,
        due_date=act_in.due_date,
        remarks=act_in.remarks,
        created_by=current_user.full_name
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)

    return format_activity_out(activity)

@router.put("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int,
    act_in: ActivityUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    if activity.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this activity.")

    if act_in.room_id is not None:
        if act_in.room_id > 0:
            room = db.query(Room).filter(Room.id == act_in.room_id).first()
            if not room or room.teacher_id != teacher.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid room_id: You do not own this room.")
            activity.room_id = room.id
        else:
            activity.room_id = None

    if act_in.title is not None:
        activity.title = act_in.title.strip()
    if act_in.description is not None:
        activity.description = act_in.description.strip()
    if act_in.type is not None:
        activity.type = act_in.type.upper()
    if act_in.status is not None:
        activity.status = act_in.status
    if act_in.marks_obtained is not None:
        activity.marks_obtained = act_in.marks_obtained
    if act_in.max_marks is not None:
        activity.max_marks = act_in.max_marks
    if act_in.due_date is not None:
        activity.due_date = act_in.due_date
    if act_in.remarks is not None:
        activity.remarks = act_in.remarks

    db.commit()
    db.refresh(activity)
    return format_activity_out(activity)

@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    if activity.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this activity.")

    db.delete(activity)
    db.commit()
    return {"message": "Activity deleted successfully", "id": activity_id}

# ================= LEGACY ACTIVITY ENDPOINTS (PRESERVED) =================

@router.post("/seminar", response_model=ActivityOut)
def create_seminar(
    seminar: SeminarCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    student = db.query(Student).filter(Student.id == seminar.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    act = Activity(
        teacher_id=teacher.id,
        student_id=seminar.student_id,
        type=ActivityType.SEMINAR,
        title=f"Seminar: {seminar.topic}",
        description=f"Presentation on {seminar.topic}",
        status=ActivityStatus.COMPLETED if seminar.marks_obtained and seminar.marks_obtained > 0 else ActivityStatus.PENDING,
        marks_obtained=seminar.marks_obtained,
        max_marks=seminar.max_marks,
        remarks=seminar.remarks,
        due_date=seminar.seminar_date,
        created_by=current_user.full_name
    )
    db.add(act)
    db.commit()
    db.refresh(act)

    sem_det = SeminarDetail(
        activity_id=act.id,
        topic=seminar.topic,
        seminar_date=seminar.seminar_date,
        presentation_mode=seminar.presentation_mode
    )
    db.add(sem_det)
    db.commit()
    db.refresh(act)

    return format_activity_out(act)

@router.post("/assignment", response_model=ActivityOut)
def create_assignment(
    assignment: AssignmentCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    act = Activity(
        teacher_id=teacher.id,
        student_id=assignment.student_id,
        type=ActivityType.ASSIGNMENT,
        title=assignment.title,
        status=ActivityStatus.SUBMITTED,
        max_marks=assignment.max_marks,
        remarks=assignment.remarks,
        due_date=assignment.due_date,
        created_by=current_user.full_name
    )
    db.add(act)
    db.commit()
    db.refresh(act)

    ass_det = AssignmentDetail(
        activity_id=act.id,
        unit=assignment.unit,
        submission_status="Submitted",
        submitted_at=datetime.utcnow().strftime("%d/%m/%Y"),
        feedback=assignment.remarks
    )
    db.add(ass_det)
    db.commit()
    db.refresh(act)

    return format_activity_out(act)

@router.post("/pbl", response_model=ActivityOut)
def create_pbl(
    pbl: PblCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    act = Activity(
        teacher_id=teacher.id,
        student_id=pbl.student_id,
        type=ActivityType.PBL,
        title=f"PBL Project: {pbl.project_title}",
        description=pbl.description,
        status=ActivityStatus.IN_PROGRESS if pbl.progress_percentage < 100 else ActivityStatus.COMPLETED,
        due_date=pbl.deadline,
        remarks=pbl.remarks,
        created_by=current_user.full_name
    )
    db.add(act)
    db.commit()
    db.refresh(act)

    pbl_det = PblDetail(
        activity_id=act.id,
        guide_name=pbl.guide_name,
        progress_percentage=pbl.progress_percentage,
        start_date=pbl.start_date or datetime.utcnow().strftime("%d/%m/%Y"),
        deadline=pbl.deadline
    )
    db.add(pbl_det)
    db.commit()
    db.refresh(act)

    return format_activity_out(act)

@router.post("/pgl", response_model=ActivityOut)
def create_pgl(
    pgl: PglCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    act = Activity(
        teacher_id=teacher.id,
        student_id=pgl.student_id,
        type=ActivityType.PGL,
        title=pgl.activity_title,
        status=ActivityStatus.COMPLETED,
        marks_obtained=pgl.marks_obtained,
        due_date=pgl.activity_date,
        remarks=pgl.remarks,
        created_by=current_user.full_name
    )
    db.add(act)
    db.commit()
    db.refresh(act)

    pgl_det = PglDetail(
        activity_id=act.id,
        activity_date=pgl.activity_date,
        participation_level=pgl.participation_level
    )
    db.add(pgl_det)
    db.commit()
    db.refresh(act)

    return format_activity_out(act)

@router.post("/generic", response_model=ActivityOut)
def create_generic_activity(
    activity: GenericActivityCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    act = Activity(
        teacher_id=teacher.id,
        student_id=activity.student_id,
        type=ActivityType.OTHER,
        title=activity.title,
        status=ActivityStatus.COMPLETED,
        due_date=activity.date or datetime.utcnow().strftime("%d/%m/%Y"),
        remarks=activity.remarks,
        created_by=current_user.full_name
    )
    db.add(act)
    db.commit()
    db.refresh(act)
    return format_activity_out(act)
