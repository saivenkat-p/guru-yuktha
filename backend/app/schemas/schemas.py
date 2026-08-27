from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class TokenPayload(BaseModel):
    sub: Optional[int] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignUpRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "TEACHER"
    # Teacher fields
    designation: Optional[str] = None
    department: Optional[str] = None
    college_name: Optional[str] = None
    employee_code: Optional[str] = None
    # Learner fields
    roll_number: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    phone: Optional[str] = None

# User, Teacher & Learner
class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class TeacherOut(BaseModel):
    id: int
    user_id: int
    employee_code: Optional[str]
    department: str
    designation: str
    college_name: str
    user: UserOut

    class Config:
        from_attributes = True

class LearnerOut(BaseModel):
    id: int
    user_id: int
    learner_id: str
    roll_number: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    department: Optional[str] = None
    college_name: Optional[str] = None
    phone: Optional[str] = None
    user: UserOut

    class Config:
        from_attributes = True

class AuthMeResponse(BaseModel):
    user: UserOut
    role: str
    teacher: Optional[TeacherOut] = None
    learner: Optional[LearnerOut] = None

    # Backward compatibility fields for legacy /auth/me consumer
    id: Optional[int] = None
    employee_code: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    college_name: Optional[str] = None

    class Config:
        from_attributes = True

class TeacherProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    college_name: Optional[str] = None
    employee_code: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None

class LearnerProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    roll_number: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    department: Optional[str] = None
    college_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None

# Room & Membership Schemas (Phase 2)
class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: Optional[str] = "PRIVATE" # PRIVATE or PUBLIC

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[str] = None
    is_active: Optional[bool] = None

class RoomOut(BaseModel):
    id: int
    teacher_id: int
    name: str
    description: Optional[str] = None
    code: str
    visibility: str = "PRIVATE"
    is_active: bool = True
    active_members_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RoomMembershipCreate(BaseModel):
    user_id: Optional[int] = None
    learner_id: Optional[int] = None
    role: Optional[str] = "MEMBER"

class RoomMembershipOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    learner_id: Optional[int] = None
    role: str = "MEMBER"
    status: str = "ACTIVE"
    joined_at: datetime
    created_at: datetime
    user: Optional[UserOut] = None
    learner: Optional[LearnerOut] = None
    room: Optional[RoomOut] = None

    class Config:
        from_attributes = True

# Folder Schemas (Phase 3)
class FolderCreate(BaseModel):
    name: str
    description: Optional[str] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class FolderOut(BaseModel):
    id: int
    room_id: int
    name: str
    description: Optional[str] = None
    is_active: bool = True
    resources_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Resource Schemas (Phase 3)
class ResourceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    folder_id: Optional[int] = None
    resource_type: Optional[str] = "PDF"
    file_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[str] = None
    visibility: Optional[str] = "ROOM_ONLY" # PUBLIC or ROOM_ONLY

class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    folder_id: Optional[int] = None
    resource_type: Optional[str] = None
    file_url: Optional[str] = None
    visibility: Optional[str] = None
    is_active: Optional[bool] = None

class ResourceOut(BaseModel):
    id: int
    room_id: int
    folder_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    resource_type: str = "PDF"
    file_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[str] = None
    visibility: str = "ROOM_ONLY"
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    folder_name: Optional[str] = None
    room_name: Optional[str] = None
    room_code: Optional[str] = None
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True

# Evidence
class EvidenceFileOut(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_size: str
    mime_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Activity Details
class SeminarDetailOut(BaseModel):
    id: int
    topic: str
    seminar_date: str
    presentation_mode: str

    class Config:
        from_attributes = True

class AssignmentDetailOut(BaseModel):
    id: int
    unit: Optional[str]
    submission_status: str
    submitted_at: Optional[str]
    feedback: Optional[str]

    class Config:
        from_attributes = True

class PblDetailOut(BaseModel):
    id: int
    guide_name: Optional[str]
    team_name: Optional[str]
    progress_percentage: int
    start_date: Optional[str]
    deadline: Optional[str]

    class Config:
        from_attributes = True

class PglDetailOut(BaseModel):
    id: int
    activity_date: Optional[str]
    participation_level: str

    class Config:
        from_attributes = True

# Activity Out
class ActivityOut(BaseModel):
    id: int
    student_id: int
    class_id: Optional[int]
    type: str
    title: str
    description: Optional[str]
    status: str
    marks_obtained: Optional[float]
    max_marks: Optional[float]
    remarks: Optional[str]
    due_date: Optional[str]
    created_at: datetime
    seminar_detail: Optional[SeminarDetailOut] = None
    assignment_detail: Optional[AssignmentDetailOut] = None
    pbl_detail: Optional[PblDetailOut] = None
    pgl_detail: Optional[PglDetailOut] = None
    evidence_files: List[EvidenceFileOut] = []

    class Config:
        from_attributes = True

# Student Schemas
class StudentBase(BaseModel):
    name: str
    roll_number: str
    course: str
    semester: str
    department: Optional[str] = "Arts & Humanities"
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[str] = "GOOD"

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None

class StudentOut(StudentBase):
    id: int
    created_at: datetime
    overall_progress: Optional[int] = 85
    attendance_percentage: Optional[int] = 88
    pending_activities_count: Optional[int] = 0

    class Config:
        from_attributes = True

class StudentProfileOut(StudentOut):
    seminars_count: str = "4 / 5"
    seminars_status: str = "Completed"
    assignments_count: str = "6 / 6"
    assignments_status: str = "Completed"
    pbl_count: str = "1 / 2"
    pbl_status: str = "In Progress"
    pgl_count: str = "4 / 5"
    pgl_status: str = "Completed"
    other_count: str = "3 / 4"
    other_status: str = "In Progress"
    activities: List[ActivityOut] = []

# Quick Action Forms Input
class SeminarCreate(BaseModel):
    student_id: int
    topic: str
    seminar_date: str
    presentation_mode: str = "Offline"
    marks_obtained: Optional[float] = 9.0
    max_marks: Optional[float] = 10.0
    remarks: Optional[str] = None

class AssignmentCreate(BaseModel):
    title: str
    student_id: int
    course: Optional[str] = "B.A. (HEP) II Sem"
    unit: Optional[str] = "Unit II"
    due_date: str
    max_marks: float = 10.0
    remarks: Optional[str] = None

class PblCreate(BaseModel):
    project_title: str
    student_id: int
    description: Optional[str] = None
    guide_name: Optional[str] = "Md. Shahazadi Begum"
    start_date: Optional[str] = None
    deadline: str
    progress_percentage: int = 25
    remarks: Optional[str] = None

class PglCreate(BaseModel):
    activity_title: str
    student_id: int
    activity_date: str
    participation_level: str = "HIGH"
    marks_obtained: Optional[float] = 9.0
    remarks: Optional[str] = None

class GenericActivityCreate(BaseModel):
    title: str
    student_id: int
    type: str = "OTHER"
    date: Optional[str] = None
    remarks: Optional[str] = None

# Attendance
class AttendanceRecordInput(BaseModel):
    student_id: int
    status: str = "PRESENT" # PRESENT, ABSENT, LATE, EXCUSED
    remarks: Optional[str] = None

class AttendanceBatchCreate(BaseModel):
    date: str
    period: str = "Period 1"
    class_name: str = "B.A. (HEP) II Sem"
    records: List[AttendanceRecordInput]

class AttendanceOut(BaseModel):
    id: int
    student_id: int
    date: str
    period: str
    status: str
    remarks: Optional[str]

    class Config:
        from_attributes = True

# Materials
class MaterialCreate(BaseModel):
    title: str
    description: Optional[str] = None
    course: str = "B.A. (HEP) II Sem"
    semester: str = "II Sem"
    unit: str = "Unit II"
    type: str = "NOTES" # NOTES, PPT, VIDEO, QUESTION_BANK, LINK, OTHER
    file_url: Optional[str] = None

class MaterialOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    course: str
    semester: str
    unit: str
    type: str
    file_path: Optional[str]
    file_url: Optional[str]
    file_size: str
    uploaded_by: str
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard Summary
class DashboardSummary(BaseModel):
    teacher_name: str = "Md. Shahazadi Begum"
    designation: str = "Lecturer in English"
    college_name: str = "GDC Ramachandrapuram"
    date_str: str = "Today, 13 May 2025"
    unread_notifications_count: int = 3
    
    total_students: int = 48
    seminars_completed: int = 32
    seminars_total: int = 48
    assignments_completed: int = 38
    assignments_total: int = 48
    pbl_completed: int = 25
    pbl_total: int = 48
    pgl_completed: int = 30
    pgl_total: int = 48
    other_completed: int = 22
    other_total: int = 48

class AttentionStudent(BaseModel):
    id: int
    name: str
    roll_number: str
    course: str
    progress_percentage: int
    status: str
    pending_reason: str
    avatar_initials: str
    avatar_color: str

class ClassInsights(BaseModel):
    overall_progress: int = 76
    attendance_rate: int = 82
    assignments_rate: int = 84
    seminars_rate: int = 71
    pbl_rate: int = 62
    pgl_rate: int = 79
