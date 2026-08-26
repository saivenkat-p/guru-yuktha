import os
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.models import (
    User, Teacher, Class, Student, Enrollment, Activity,
    SeminarDetail, AssignmentDetail, PblDetail, PglDetail,
    Attendance, Material, EvidenceFile, Notification,
    UserRole, StudentStatus, ActivityType, ActivityStatus,
    PresentationMode, ParticipationLevel, AttendanceStatus, MaterialType
)

def seed_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        print("Seeding Guru Yuktha Database...")

        # 1. Create Default Teacher User
        teacher_user = User(
            email="teacher@guruyuktha.edu",
            hashed_password=get_password_hash("teacher123"),
            full_name="Md. Shahazadi Begum",
            role=UserRole.TEACHER,
            avatar_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80"
        )
        db.add(teacher_user)
        db.commit()
        db.refresh(teacher_user)

        teacher_profile = Teacher(
            user_id=teacher_user.id,
            employee_code="EMP-2024-ENG",
            department="English",
            designation="Lecturer in English",
            college_name="GDC Ramachandrapuram"
        )
        db.add(teacher_profile)
        db.commit()

        # 2. Create Default Classes
        class_hep = Class(
            teacher_id=teacher_profile.id,
            name="B.A. (HEP) II Sem",
            course="B.A. (HEP)",
            semester="II Sem",
            section="A",
            subject="General English"
        )
        class_bsc = Class(
            teacher_id=teacher_profile.id,
            name="B.Sc. (MPCs) II Sem",
            course="B.Sc. (MPCs)",
            semester="II Sem",
            section="B",
            subject="Technical Communication"
        )
        db.add_all([class_hep, class_bsc])
        db.commit()

        # 3. Reference & Additional Students List (Exact names from UI + realistic roster to make 48)
        reference_students = [
            {"name": "A. Ravi", "roll": "2201A1001", "course": "B.A. (HEP) II Sem", "status": StudentStatus.GOOD, "phone": "9876543210"},
            {"name": "P. Sravani", "roll": "2201A1002", "course": "B.A. (HEP) II Sem", "status": StudentStatus.NEEDS_ATTENTION, "phone": "9876543211"},
            {"name": "K. Sai Kumar", "roll": "2201A1003", "course": "B.A. (HEP) II Sem", "status": StudentStatus.GOOD, "phone": "9876543212"},
            {"name": "M. Zahid", "roll": "2201A1004", "course": "B.A. (HEP) II Sem", "status": StudentStatus.CRITICAL, "phone": "9876543213"},
            {"name": "S. Nandini", "roll": "2201A1005", "course": "B.A. (HEP) II Sem", "status": StudentStatus.GOOD, "phone": "9876543214"},
            {"name": "P. Venkatesh", "roll": "2201A1006", "course": "B.A. (HEP) II Sem", "status": StudentStatus.GOOD, "phone": "9876543215"},
            {"name": "Sk. Kareem", "roll": "2201A1007", "course": "B.A. (HEP) II Sem", "status": StudentStatus.NEEDS_ATTENTION, "phone": "9876543216"},
            {"name": "Y. Swapna", "roll": "2201A1008", "course": "B.A. (HEP) II Sem", "status": StudentStatus.GOOD, "phone": "9876543217"},
            {"name": "B. Rajesh", "roll": "2201A1009", "course": "B.A. (HEP) II Sem", "status": StudentStatus.GOOD, "phone": "9876543218"},
            {"name": "Ch. Anusha", "roll": "2201A1010", "course": "B.A. (HEP) II Sem", "status": StudentStatus.NEEDS_ATTENTION, "phone": "9876543219"},
            {"name": "D. Manoj", "roll": "2201A1011", "course": "B.A. (HEP) II Sem", "status": StudentStatus.GOOD, "phone": "9876543220"},
            {"name": "E. Divya", "roll": "2201A1012", "course": "B.A. (HEP) II Sem", "status": StudentStatus.GOOD, "phone": "9876543221"},
        ]

        # Extend up to 48 students with structured variation
        first_names = ["G. Karthik", "H. Priya", "I. Suresh", "J. Bhavani", "K. Naresh", "L. Kavitha", 
                       "M. Praveen", "N. Sneha", "O. Vamsi", "P. Renu", "Q. Tarun", "R. Swathi",
                       "S. Vikram", "T. Harika", "U. Dinesh", "V. Ramya", "W. Sandeep", "X. Meena",
                       "Y. Ashok", "Z. Lakshmi", "A. Mahesh", "B. Teja", "C. Keerthi", "D. Nithin",
                       "E. Archana", "F. Pavan", "G. Sirisha", "H. Vinay", "I. Preeti", "J. Gopi",
                       "K. Sravanti", "L. Charan", "M. Deepika", "N. Lokesh", "O. Lavanya", "P. Ajay"]
        
        for i, name in enumerate(first_names):
            roll_num = f"2201A10{13+i}"
            status = StudentStatus.CRITICAL if i in [2, 10] else (StudentStatus.NEEDS_ATTENTION if i % 4 == 0 else StudentStatus.GOOD)
            reference_students.append({
                "name": name,
                "roll": roll_num,
                "course": "B.A. (HEP) II Sem" if i % 2 == 0 else "B.Sc. (MPCs) II Sem",
                "status": status,
                "phone": f"98765432{22+i}"
            })

        db_students = []
        for s in reference_students:
            student = Student(
                name=s["name"],
                roll_number=s["roll"],
                course=s["course"],
                semester="II Sem",
                department="English & Languages",
                phone=s["phone"],
                status=s["status"]
            )
            db.add(student)
            db_students.append(student)

        db.commit()

        # Enroll all students into class_hep
        for st in db_students:
            enr = Enrollment(class_id=class_hep.id, student_id=st.id)
            db.add(enr)
        db.commit()

        print(f"  - Seeded {len(db_students)} Students")

        # 4. Create Activities for A. Ravi (Featured Student in UI)
        ravi = db_students[0] # A. Ravi

        # Seminars for Ravi (4 / 5 Completed)
        seminar_topics = [
            ("The Importance of Communication", "13/05/2025", 9.0, PresentationMode.OFFLINE, ActivityStatus.COMPLETED),
            ("Phonetics and Pronunciation Skills", "05/05/2025", 8.5, PresentationMode.OFFLINE, ActivityStatus.COMPLETED),
            ("Role of Literature in Society", "28/04/2025", 9.0, PresentationMode.HYBRID, ActivityStatus.COMPLETED),
            ("Effective Presentation Techniques", "20/04/2025", 8.0, PresentationMode.ONLINE, ActivityStatus.COMPLETED),
            ("Future Trends in Digital Communication", "25/05/2025", 0.0, PresentationMode.OFFLINE, ActivityStatus.PENDING),
        ]
        for topic, date_str, marks, mode, stat in seminar_topics:
            act = Activity(
                student_id=ravi.id,
                class_id=class_hep.id,
                type=ActivityType.SEMINAR,
                title=f"Seminar: {topic}",
                description=f"Presentation on {topic}",
                status=stat,
                marks_obtained=marks if stat == ActivityStatus.COMPLETED else None,
                max_marks=10.0,
                remarks="Excellent presentation and content." if stat == ActivityStatus.COMPLETED else "Scheduled",
                due_date=date_str,
                created_by="Md. Shahazadi Begum"
            )
            db.add(act)
            db.commit()
            db.refresh(act)

            sem_det = SeminarDetail(
                activity_id=act.id,
                topic=topic,
                seminar_date=date_str,
                presentation_mode=mode
            )
            db.add(sem_det)

            # Add Evidence for Ravi's primary seminar
            if topic == "The Importance of Communication":
                e1 = EvidenceFile(
                    activity_id=act.id,
                    file_name="Seminar_Ravi.pdf",
                    file_path="/uploads/Seminar_Ravi.pdf",
                    file_size="1.2 MB",
                    mime_type="application/pdf"
                )
                e2 = EvidenceFile(
                    activity_id=act.id,
                    file_name="Ravi_Seminar.jpg",
                    file_path="/uploads/Ravi_Seminar.jpg",
                    file_size="1.5 MB",
                    mime_type="image/jpeg"
                )
                db.add_all([e1, e2])

        db.commit()

        # Assignments for Ravi (6 / 6 Completed)
        assignment_titles = [
            ("Assignment 1: Unit I Essay Analysis", "02/05/2025", 10.0),
            ("Assignment 2: Grammar & Sentence Structure", "10/05/2025", 9.5),
            ("Assignment 3: Vocabulary & Contextual Usage", "12/05/2025", 9.0),
            ("Assignment 4: Short Story Review — Edward P. Jones", "14/04/2025", 8.5),
            ("Assignment 5: Report Writing & Formats", "22/04/2025", 9.0),
            ("Assignment 6: Reading Comprehension Practice", "29/04/2025", 9.5),
        ]
        for title, date_str, marks in assignment_titles:
            act = Activity(
                student_id=ravi.id,
                class_id=class_hep.id,
                type=ActivityType.ASSIGNMENT,
                title=title,
                status=ActivityStatus.COMPLETED,
                marks_obtained=marks,
                max_marks=10.0,
                remarks="Submitted on time with complete solutions.",
                due_date=date_str
            )
            db.add(act)
            db.commit()

            ass_det = AssignmentDetail(
                activity_id=act.id,
                unit="Unit II",
                submission_status="Submitted",
                submitted_at=date_str,
                feedback="Well structured answers."
            )
            db.add(ass_det)
        db.commit()

        # PBL Projects for Ravi (1 / 2 In Progress)
        pbl_data = [
            ("English Language Lab Interactive Project", 100, ActivityStatus.COMPLETED, "Completed"),
            ("Community English Literacy Survey & Report", 50, ActivityStatus.IN_PROGRESS, "In Progress")
        ]
        for pbl_title, prog, stat, stat_lbl in pbl_data:
            act = Activity(
                student_id=ravi.id,
                class_id=class_hep.id,
                type=ActivityType.PBL,
                title=f"PBL Project: {pbl_title}",
                status=stat,
                marks_obtained=9.0 if stat == ActivityStatus.COMPLETED else None,
                max_marks=10.0,
                due_date="30/05/2025"
            )
            db.add(act)
            db.commit()

            pbl_det = PblDetail(
                activity_id=act.id,
                guide_name="Md. Shahazadi Begum",
                team_name="Group Alpha",
                progress_percentage=prog,
                start_date="01/05/2025",
                deadline="30/05/2025"
            )
            db.add(pbl_det)
        db.commit()

        # PGL Activities for Ravi (4 / 5 Completed)
        for i in range(1, 6):
            stat = ActivityStatus.COMPLETED if i <= 4 else ActivityStatus.PENDING
            act = Activity(
                student_id=ravi.id,
                class_id=class_hep.id,
                type=ActivityType.PGL,
                title=f"PGL Group Discussion #{i}",
                status=stat,
                marks_obtained=9.0 if stat == ActivityStatus.COMPLETED else None,
                max_marks=10.0,
                due_date="08/05/2025"
            )
            db.add(act)
            db.commit()

            pgl_det = PglDetail(
                activity_id=act.id,
                activity_date="08/05/2025",
                participation_level=ParticipationLevel.HIGH
            )
            db.add(pgl_det)
        db.commit()

        # Other Activities for Ravi (3 / 4 In Progress/Completed)
        other_list = [
            ("Workshop on Soft Skills", ActivityStatus.COMPLETED, 9.0),
            ("Departmental Debate Competition", ActivityStatus.COMPLETED, 8.5),
            ("English Literary Club Presentation", ActivityStatus.COMPLETED, 9.0),
            ("Annual Cultural Day Poetry Recital", ActivityStatus.IN_PROGRESS, None)
        ]
        for otitle, stat, marks in other_list:
            act = Activity(
                student_id=ravi.id,
                class_id=class_hep.id,
                type=ActivityType.OTHER,
                title=otitle,
                status=stat,
                marks_obtained=marks,
                max_marks=10.0,
                due_date="15/05/2025"
            )
            db.add(act)
        db.commit()

        # Seed Activity records for the remaining 47 students to generate realistic class stats:
        # Total Students: 48, Seminars Completed: 32/48, Assignments: 38/48, PBL: 25/48, PGL: 30/48, Other: 22/48
        for index, student in enumerate(db_students[1:], start=1):
            # Seminars (32 total completed out of 48)
            sem_stat = ActivityStatus.COMPLETED if index < 31 else ActivityStatus.PENDING
            s_act = Activity(
                student_id=student.id,
                class_id=class_hep.id,
                type=ActivityType.SEMINAR,
                title=f"Seminar: Communication Skills",
                status=sem_stat,
                marks_obtained=8.0 if sem_stat == ActivityStatus.COMPLETED else None,
                max_marks=10.0,
                due_date="13/05/2025"
            )
            db.add(s_act)
            db.commit()

            db.add(SeminarDetail(
                activity_id=s_act.id,
                topic="Effective Communication Skills",
                seminar_date="13/05/2025",
                presentation_mode=PresentationMode.OFFLINE
            ))

            # Assignments (38 completed out of 48)
            ass_stat = ActivityStatus.COMPLETED if index < 37 else ActivityStatus.PENDING
            a_act = Activity(
                student_id=student.id,
                class_id=class_hep.id,
                type=ActivityType.ASSIGNMENT,
                title="Unit II Grammar Assignment",
                status=ass_stat,
                marks_obtained=8.5 if ass_stat == ActivityStatus.COMPLETED else None,
                max_marks=10.0,
                due_date="10/05/2025"
            )
            db.add(a_act)
            db.commit()
            db.add(AssignmentDetail(activity_id=a_act.id, unit="Unit II", submission_status="Submitted"))

            # PBL Projects (25 completed/in-progress out of 48)
            pbl_stat = ActivityStatus.IN_PROGRESS if index < 24 else ActivityStatus.PENDING
            p_act = Activity(
                student_id=student.id,
                class_id=class_hep.id,
                type=ActivityType.PBL,
                title="Language & Culture Research Project",
                status=pbl_stat,
                due_date="30/05/2025"
            )
            db.add(p_act)
            db.commit()
            db.add(PblDetail(activity_id=p_act.id, guide_name="Md. Shahazadi Begum", progress_percentage=50 if pbl_stat == ActivityStatus.IN_PROGRESS else 0))

            # PGL Activities (30 completed out of 48)
            pgl_stat = ActivityStatus.COMPLETED if index < 29 else ActivityStatus.PENDING
            pg_act = Activity(
                student_id=student.id,
                class_id=class_hep.id,
                type=ActivityType.PGL,
                title="Group Reading Activity",
                status=pgl_stat,
                due_date="08/05/2025"
            )
            db.add(pg_act)
            db.commit()
            db.add(PglDetail(activity_id=pg_act.id, activity_date="08/05/2025"))

            # Other Activities (22 completed out of 48)
            oth_stat = ActivityStatus.COMPLETED if index < 21 else ActivityStatus.PENDING
            o_act = Activity(
                student_id=student.id,
                class_id=class_hep.id,
                type=ActivityType.OTHER,
                title="Literary Club Quiz",
                status=oth_stat,
                due_date="15/05/2025"
            )
            db.add(o_act)

        db.commit()
        print("  - Seeded Student Activities & Progress Stats")

        # 5. Seed Attendance Data
        dates = ["10/05/2025", "11/05/2025", "12/05/2025", "13/05/2025"]
        for st in db_students:
            for d in dates:
                # Zahid and Kareem have lower attendance for risk triggers
                if st.name in ["M. Zahid", "Sk. Kareem"] and d in ["11/05/2025", "12/05/2025"]:
                    att_status = AttendanceStatus.ABSENT
                else:
                    att_status = AttendanceStatus.PRESENT
                
                db.add(Attendance(
                    class_id=class_hep.id,
                    student_id=st.id,
                    date=d,
                    period="Period 1",
                    status=att_status
                ))
        db.commit()
        print("  - Seeded Attendance Records")

        # 6. Seed Materials (Exact list from Reference UI Screen 5)
        materials_data = [
            {
                "title": "The First Day - Notes.pdf",
                "description": "Unit II — The First Day Notes",
                "course": "B.A. (HEP) II Sem",
                "semester": "II Sem",
                "unit": "Unit II",
                "type": MaterialType.NOTES,
                "file_size": "1.3 MB",
                "uploaded_by": "Md. Shahazadi Begum",
                "created_at": datetime.utcnow() - timedelta(days=3)
            },
            {
                "title": "The First Day - PPT.pptx",
                "description": "Unit II — The First Day Presentation",
                "course": "B.A. (HEP) II Sem",
                "semester": "II Sem",
                "unit": "Unit II",
                "type": MaterialType.PPT,
                "file_size": "2.8 MB",
                "uploaded_by": "Md. Shahazadi Begum",
                "created_at": datetime.utcnow() - timedelta(days=5)
            },
            {
                "title": "Edward P. Jones - Short Story.mp4",
                "description": "Unit II — The First Day Video Lecture",
                "course": "B.A. (HEP) II Sem",
                "semester": "II Sem",
                "unit": "Unit II",
                "type": MaterialType.VIDEO,
                "file_size": "25 MB",
                "uploaded_by": "Md. Shahazadi Begum",
                "created_at": datetime.utcnow() - timedelta(days=7)
            },
            {
                "title": "Question Bank - Unit II.pdf",
                "description": "Unit II — The First Day Question Bank",
                "course": "B.A. (HEP) II Sem",
                "semester": "II Sem",
                "unit": "Unit II",
                "type": MaterialType.QUESTION_BANK,
                "file_size": "1.1 MB",
                "uploaded_by": "Md. Shahazadi Begum",
                "created_at": datetime.utcnow() - timedelta(days=8)
            },
            {
                "title": "Reference Link - Short Stories",
                "description": "Unit II — The First Day External Reference",
                "course": "B.A. (HEP) II Sem",
                "semester": "II Sem",
                "unit": "Unit II",
                "type": MaterialType.LINK,
                "file_url": "https://example.edu/literature/short-stories",
                "file_size": "Link",
                "uploaded_by": "Md. Shahazadi Begum",
                "created_at": datetime.utcnow() - timedelta(days=10)
            }
        ]
        for m in materials_data:
            mat = Material(
                class_id=class_hep.id,
                title=m["title"],
                description=m["description"],
                course=m["course"],
                semester=m["semester"],
                unit=m["unit"],
                type=m["type"],
                file_size=m["file_size"],
                file_url=m.get("file_url"),
                uploaded_by=m["uploaded_by"],
                created_at=m["created_at"]
            )
            db.add(mat)
        db.commit()
        print("  - Seeded Learning Materials")

        # 7. Seed Notifications
        notifications_data = [
            {"title": "Overdue Assignments Warning", "message": "3 students have pending assignments for Unit II.", "type": "OVERDUE"},
            {"title": "Upcoming Seminar Scheduled", "message": "Future Trends in Digital Communication seminar scheduled tomorrow.", "type": "SEMINAR_ALERT"},
            {"title": "Attendance Alert", "message": "M. Zahid attendance fell below 65% threshold.", "type": "ATTENDANCE_WARNING"}
        ]
        for n in notifications_data:
            db.add(Notification(
                teacher_id=teacher_profile.id,
                title=n["title"],
                message=n["message"],
                type=n["type"],
                is_read=False
            ))
        db.commit()
        print("  - Seeded Notifications")

        print("Database seeding completed successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
