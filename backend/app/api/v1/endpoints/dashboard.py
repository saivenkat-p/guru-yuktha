from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_teacher
from app.models.models import (
    Student, Activity, Attendance, Teacher, User, Room, RoomMembership, Enrollment, Class,
    ActivityType, ActivityStatus, StudentStatus
)
from app.schemas.schemas import DashboardSummary, AttentionStudent, ClassInsights
from app.api.v1.endpoints.students import compute_real_student_metrics

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

def get_teacher_students_query(teacher: Teacher, db: Session):
    # Students enrolled in teacher classes or tracked in teacher rooms
    class_student_ids = db.query(Enrollment.student_id).join(Class).filter(Class.teacher_id == teacher.id)
    room_student_ids = db.query(RoomMembership.learner_id).join(Room).filter(
        Room.teacher_id == teacher.id,
        RoomMembership.status == "ACTIVE"
    )
    return db.query(Student).filter(
        (Student.id.in_(class_student_ids)) | (Student.id.in_(room_student_ids)),
        Student.status != StudentStatus.ARCHIVED
    )

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    teacher_name = current_user.full_name
    designation = teacher.designation or "Faculty"
    college_name = teacher.college_name or "Academic Institution"

    active_students = get_teacher_students_query(teacher, db).all()
    total_students = len(active_students)

    # Scoped activity counts for this teacher
    seminars_comp = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.SEMINAR,
        Activity.status == ActivityStatus.COMPLETED
    ).count()
    seminars_tot = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.SEMINAR
    ).count()

    assign_comp = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.ASSIGNMENT,
        Activity.status.in_([ActivityStatus.COMPLETED, ActivityStatus.SUBMITTED])
    ).count()
    assign_tot = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.ASSIGNMENT
    ).count()

    pbl_comp = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.PBL,
        Activity.status.in_([ActivityStatus.COMPLETED, ActivityStatus.IN_PROGRESS])
    ).count()
    pbl_tot = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.PBL
    ).count()

    pgl_comp = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.PGL,
        Activity.status == ActivityStatus.COMPLETED
    ).count()
    pgl_tot = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.PGL
    ).count()

    other_comp = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.OTHER,
        Activity.status.in_([ActivityStatus.COMPLETED, ActivityStatus.IN_PROGRESS])
    ).count()
    other_tot = db.query(Activity).filter(
        Activity.teacher_id == teacher.id,
        Activity.type == ActivityType.OTHER
    ).count()

    return DashboardSummary(
        teacher_name=teacher_name,
        designation=designation,
        college_name=college_name,
        date_str=f"Today, {datetime.utcnow().strftime('%d %b %Y')}",
        unread_notifications_count=0,
        total_students=total_students,
        seminars_completed=seminars_comp,
        seminars_total=seminars_tot,
        assignments_completed=assign_comp,
        assignments_total=assign_tot,
        pbl_completed=pbl_comp,
        pbl_total=pbl_tot,
        pgl_completed=pgl_comp,
        pgl_total=pgl_tot,
        other_completed=other_comp,
        other_total=other_tot
    )

@router.get("/attention", response_model=List[AttentionStudent])
def get_students_needing_attention(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    students_query = get_teacher_students_query(teacher, db)

    attention_students = students_query.filter(
        Student.status.in_([StudentStatus.NEEDS_ATTENTION, StudentStatus.CRITICAL])
    ).limit(6).all()

    if not attention_students:
        active = students_query.all()
        scored = []
        for s in active:
            prog, att, pending = compute_real_student_metrics(s.id, db)
            scored.append((prog, s, pending))
        scored.sort(key=lambda x: x[0])
        attention_students = [x[1] for x in scored[:5]]

    results = []
    colors = ["bg-red-100 text-red-700", "bg-amber-100 text-amber-700", "bg-purple-100 text-purple-700"]
    
    for idx, s in enumerate(attention_students):
        parts = s.name.split(" ")
        initials = "".join([p[0] for p in parts if p])[:2].upper()
        prog, att_pct, pending_cnt = compute_real_student_metrics(s.id, db)
        reason = f"{pending_cnt} activities pending" if pending_cnt > 0 else "Needs progress review"
        
        results.append(AttentionStudent(
            id=s.id,
            name=s.name,
            roll_number=s.roll_number,
            course=s.course,
            progress_percentage=prog,
            status=s.status,
            pending_reason=reason,
            avatar_initials=initials,
            avatar_color=colors[idx % len(colors)]
        ))
    
    return results

@router.get("/insights", response_model=ClassInsights)
def get_class_insights(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = get_or_create_teacher(current_user, db)
    students = get_teacher_students_query(teacher, db).all()
    if not students:
        return ClassInsights(overall_progress=0, attendance_rate=0, assignments_rate=0, seminars_rate=0, pbl_rate=0, pgl_rate=0)

    total_progs = []
    total_atts = []
    for s in students:
        prog, att, _ = compute_real_student_metrics(s.id, db)
        total_progs.append(prog)
        total_atts.append(att)

    avg_prog = round(sum(total_progs) / len(total_progs)) if total_progs else 0
    avg_att = round(sum(total_atts) / len(total_atts)) if total_atts else 0

    return ClassInsights(
        overall_progress=avg_prog,
        attendance_rate=avg_att,
        assignments_rate=avg_prog,
        seminars_rate=avg_prog,
        pbl_rate=avg_prog,
        pgl_rate=avg_prog
    )
