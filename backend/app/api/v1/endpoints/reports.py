import io
import csv
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.models import Student, Activity, Attendance, Material, ActivityType, ActivityStatus

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

router = APIRouter()

@router.get("/student/{student_id}/pdf")
def generate_student_pdf_report(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    activities = db.query(Activity).filter(Activity.student_id == student_id).all()

    if HAS_REPORTLAB:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#4F46E5'),
            alignment=0,
            spaceAfter=6
        )

        sub_style = ParagraphStyle(
            'SubStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=12
        )

        story = []
        story.append(Paragraph("Guru Yuktha — Academic Progress Report", title_style))
        story.append(Paragraph(f"Institution: GDC Ramachandrapuram | Lecturer: Md. Shahazadi Begum", sub_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB'), spaceAfter=15))

        # Student Details Table
        student_info = [
            [Paragraph("<b>Student Name:</b>", styles['Normal']), Paragraph(student.name, styles['Normal']),
             Paragraph("<b>Roll Number:</b>", styles['Normal']), Paragraph(student.roll_number, styles['Normal'])],
            [Paragraph("<b>Course:</b>", styles['Normal']), Paragraph(student.course, styles['Normal']),
             Paragraph("<b>Status:</b>", styles['Normal']), Paragraph(student.status, styles['Normal'])]
        ]
        info_table = Table(student_info, colWidths=[110, 160, 110, 160])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F9FAFB')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 15))

        # Activities Summary Table
        story.append(Paragraph("<b>Academic Activities Summary</b>", styles['Heading2']))
        story.append(Spacer(1, 6))

        table_data = [["Title", "Type", "Status", "Date / Due", "Score"]]
        for a in activities:
            score_str = f"{a.marks_obtained} / {a.max_marks}" if a.marks_obtained is not None else "N/A"
            table_data.append([
                a.title[:35],
                a.type,
                a.status,
                a.due_date or "—",
                score_str
            ])

        act_table = Table(table_data, colWidths=[200, 80, 90, 80, 80])
        act_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        story.append(act_table)

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Report_{student.roll_number}.pdf"}
        )
    else:
        # Text fallback if ReportLab not present
        content = f"GURU YUKTHA ACADEMIC REPORT\nName: {student.name}\nRoll: {student.roll_number}\nCourse: {student.course}\n"
        return Response(content=content, media_type="text/plain")

@router.get("/class/summary/pdf")
def generate_class_summary_pdf(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    
    if HAS_REPORTLAB:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        story = [
            Paragraph("Guru Yuktha — Class Activity Summary Report", styles['Heading1']),
            Paragraph("Class: B.A. (HEP) II Sem | Department of English", styles['Normal']),
            Spacer(1, 15)
        ]

        data = [["Roll Number", "Student Name", "Course", "Progress", "Status"]]
        for s in students[:20]:
            data.append([s.roll_number, s.name, s.course, "85%", s.status])

        t = Table(data, colWidths=[90, 180, 130, 70, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=Class_Summary_Report.pdf"})
    else:
        return Response(content="Guru Yuktha Class Summary Report", media_type="text/plain")

@router.get("/export/csv")
def export_custom_csv(db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Student ID", "Roll Number", "Name", "Course", "Semester", "Status", "Total Activities"])

    students = db.query(Student).all()
    for s in students:
        act_count = db.query(Activity).filter(Activity.student_id == s.id).count()
        writer.writerow([s.id, s.roll_number, s.name, s.course, s.semester, s.status, act_count])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=GuruYuktha_Export_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
    )
