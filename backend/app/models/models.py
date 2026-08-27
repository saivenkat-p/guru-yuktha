import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    TEACHER = "TEACHER"
    LEARNER = "LEARNER"
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"

class StudentStatus(str, enum.Enum):
    GOOD = "GOOD"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    CRITICAL = "CRITICAL"
    ARCHIVED = "ARCHIVED"

class ActivityType(str, enum.Enum):
    SEMINAR = "SEMINAR"
    ASSIGNMENT = "ASSIGNMENT"
    PBL = "PBL"
    PGL = "PGL"
    OTHER = "OTHER"
    ASSESSMENT = "ASSESSMENT"

class ActivityStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    COMPLETED = "COMPLETED"
    LATE = "LATE"
    REJECTED = "REJECTED"

class PresentationMode(str, enum.Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    HYBRID = "HYBRID"

class ParticipationLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"

class MaterialType(str, enum.Enum):
    NOTES = "NOTES"
    PPT = "PPT"
    VIDEO = "VIDEO"
    QUESTION_BANK = "QUESTION_BANK"
    LINK = "LINK"
    OTHER = "OTHER"

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.TEACHER)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
    learner_profile = relationship("Learner", back_populates="user", uselist=False)
    room_memberships = relationship("RoomMembership", back_populates="user", cascade="all, delete-orphan")

# Teacher model
class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    employee_code = Column(String(100), nullable=True)
    department = Column(String(100), default="English")
    designation = Column(String(100), default="Lecturer in English")
    college_name = Column(String(255), default="GDC Ramachandrapuram")

    user = relationship("User", back_populates="teacher_profile")
    classes = relationship("Class", back_populates="teacher")
    rooms = relationship("Room", back_populates="owner", cascade="all, delete-orphan")

# Learner model (for independently registered learners)
class Learner(Base):
    __tablename__ = "learners"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    learner_id = Column(String(100), unique=True, index=True, nullable=False)  # e.g., STU-2026-000001
    roll_number = Column(String(100), nullable=True)
    course = Column(String(100), nullable=True)
    semester = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    college_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="learner_profile")
    memberships = relationship("RoomMembership", back_populates="learner", cascade="all, delete-orphan")

# Dedicated Next-Gen Room Model
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    visibility = Column(String(50), default="PRIVATE")  # PRIVATE, PUBLIC
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("Teacher", back_populates="rooms")
    memberships = relationship("RoomMembership", back_populates="room", cascade="all, delete-orphan")

# Dedicated Room Membership Model
class RoomMembership(Base):
    __tablename__ = "room_memberships"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=True, index=True)
    role = Column(String(50), default="MEMBER")
    status = Column(String(50), default="ACTIVE")  # ACTIVE, PENDING, REJECTED, REMOVED, ARCHIVED
    joined_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room = relationship("Room", back_populates="memberships")
    user = relationship("User", back_populates="room_memberships")
    learner = relationship("Learner", back_populates="memberships")

# Class model
class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    name = Column(String(100), nullable=False)  # e.g., B.A. (HEP)
    course = Column(String(100), nullable=False) # e.g., B.A. (HEP)
    semester = Column(String(50), nullable=False) # e.g., II Sem / III Sem
    section = Column(String(50), default="A")
    subject = Column(String(100), default="English")

    teacher = relationship("Teacher", back_populates="classes")
    enrollments = relationship("Enrollment", back_populates="class_obj")
    activities = relationship("Activity", back_populates="class_obj")

# Student model
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    roll_number = Column(String(100), unique=True, index=True, nullable=False)
    course = Column(String(100), nullable=False)
    semester = Column(String(50), nullable=False)
    department = Column(String(100), default="Arts & Humanities")
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    status = Column(String(50), default=StudentStatus.GOOD)
    created_at = Column(DateTime, default=datetime.utcnow)

    enrollments = relationship("Enrollment", back_populates="student")
    activities = relationship("Activity", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")

# Enrollment
class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)

    class_obj = relationship("Class", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollments")

# Base Activity
class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    type = Column(String(50), nullable=False)  # SEMINAR, ASSIGNMENT, PBL, PGL, OTHER, ASSESSMENT
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=ActivityStatus.COMPLETED)
    marks_obtained = Column(Float, nullable=True)
    max_marks = Column(Float, default=10.0)
    remarks = Column(Text, nullable=True)
    due_date = Column(String(50), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="activities")
    class_obj = relationship("Class", back_populates="activities")
    seminar_detail = relationship("SeminarDetail", back_populates="activity", uselist=False, cascade="all, delete-orphan")
    assignment_detail = relationship("AssignmentDetail", back_populates="activity", uselist=False, cascade="all, delete-orphan")
    pbl_detail = relationship("PblDetail", back_populates="activity", uselist=False, cascade="all, delete-orphan")
    pgl_detail = relationship("PglDetail", back_populates="activity", uselist=False, cascade="all, delete-orphan")
    evidence_files = relationship("EvidenceFile", back_populates="activity", cascade="all, delete-orphan")

# Detail tables
class SeminarDetail(Base):
    __tablename__ = "seminar_details"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), unique=True)
    topic = Column(String(255), nullable=False)
    seminar_date = Column(String(50), nullable=False)
    presentation_mode = Column(String(50), default=PresentationMode.OFFLINE)

    activity = relationship("Activity", back_populates="seminar_detail")

class AssignmentDetail(Base):
    __tablename__ = "assignment_details"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), unique=True)
    unit = Column(String(100), nullable=True)
    submission_status = Column(String(50), default="Submitted")
    submitted_at = Column(String(50), nullable=True)
    feedback = Column(Text, nullable=True)

    activity = relationship("Activity", back_populates="assignment_detail")

class PblDetail(Base):
    __tablename__ = "pbl_details"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), unique=True)
    guide_name = Column(String(255), nullable=True)
    team_name = Column(String(255), nullable=True)
    progress_percentage = Column(Integer, default=0) # 0, 25, 50, 75, 100
    start_date = Column(String(50), nullable=True)
    deadline = Column(String(50), nullable=True)

    activity = relationship("Activity", back_populates="pbl_detail")

class PglDetail(Base):
    __tablename__ = "pgl_details"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), unique=True)
    activity_date = Column(String(50), nullable=True)
    participation_level = Column(String(50), default=ParticipationLevel.HIGH)

    activity = relationship("Activity", back_populates="pgl_detail")

# Attendance
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(String(50), nullable=False)
    period = Column(String(50), default="Period 1")
    status = Column(String(50), default=AttendanceStatus.PRESENT)
    remarks = Column(String(255), nullable=True)

    student = relationship("Student", back_populates="attendance_records")

# Materials
class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    course = Column(String(100), default="B.A. (HEP) II Sem")
    semester = Column(String(50), default="II Sem")
    unit = Column(String(100), default="Unit II")
    type = Column(String(50), default=MaterialType.NOTES) # NOTES, PPT, VIDEO, QUESTION_BANK, LINK, OTHER
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_size = Column(String(50), default="1.2 MB")
    uploaded_by = Column(String(255), default="Md. Shahazadi Begum")
    created_at = Column(DateTime, default=datetime.utcnow)

    evidence_files = relationship("EvidenceFile", back_populates="material")

# Evidence Files
class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(String(50), default="1.0 MB")
    mime_type = Column(String(100), default="application/pdf")
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    activity = relationship("Activity", back_populates="evidence_files")
    material = relationship("Material", back_populates="evidence_files")

# Notifications
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="INFO")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
