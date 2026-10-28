from contextlib import asynccontextmanager
from pathlib import Path
from datetime import date
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # creates attendance.db + tables on first run
    yield


app = FastAPI(title="Attendance Management System", lifespan=lifespan)


# ---------- web page ----------
@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "index.html")


# ---------- helpers ----------
def get_student_or_404(db: Session, student_id: int) -> models.Student:
    student = db.get(models.Student, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    return student


def build_summary(student: models.Student, records: List[models.Attendance]) -> schemas.AttendanceSummary:
    total = len(records)
    present = sum(r.status == "present" for r in records)
    late = sum(r.status == "late" for r in records)
    absent = sum(r.status == "absent" for r in records)
    # Late counts as attended
    percentage = round((present + late) / total * 100, 2) if total else 0.0
    return schemas.AttendanceSummary(
        student_id=student.id, roll_no=student.roll_no, name=student.name,
        total_days=total, present=present, late=late, absent=absent, percentage=percentage,
    )


# ---------- students ----------
@app.post("/students", response_model=schemas.StudentOut, status_code=201)
def add_student(data: schemas.StudentCreate, db: Session = Depends(get_db)):
    if db.query(models.Student).filter_by(roll_no=data.roll_no).first():
        raise HTTPException(400, "Roll number already exists")
    student = models.Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/students", response_model=List[schemas.StudentOut])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Student).order_by(models.Student.roll_no).all()


@app.get("/students/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return get_student_or_404(db, student_id)


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = get_student_or_404(db, student_id)
    db.delete(student)
    db.commit()
    return {"message": "Student and their attendance deleted"}


# ---------- attendance ----------
@app.post("/attendance", response_model=schemas.AttendanceOut, status_code=201)
def mark_attendance(data: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    get_student_or_404(db, data.student_id)
    exists = db.query(models.Attendance).filter_by(student_id=data.student_id, date=data.date).first()
    if exists:
        raise HTTPException(400, "Attendance already marked for this student on this date")
    record = models.Attendance(
        student_id=data.student_id, date=data.date, status=data.status.value, remark=data.remark
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.put("/attendance/{record_id}", response_model=schemas.AttendanceOut)
def update_attendance(record_id: int, data: schemas.AttendanceUpdate, db: Session = Depends(get_db)):
    record = db.get(models.Attendance, record_id)
    if not record:
        raise HTTPException(404, "Record not found")
    record.status = data.status.value
    record.remark = data.remark
    db.commit()
    db.refresh(record)
    return record


@app.delete("/attendance/{record_id}")
def delete_attendance(record_id: int, db: Session = Depends(get_db)):
    record = db.get(models.Attendance, record_id)
    if not record:
        raise HTTPException(404, "Record not found")
    db.delete(record)
    db.commit()
    return {"message": "Record deleted"}


@app.get("/attendance/date/{day}", response_model=List[schemas.AttendanceOut])
def attendance_by_date(day: date, db: Session = Depends(get_db)):
    """All students' attendance for one date (YYYY-MM-DD)."""
    return db.query(models.Attendance).filter_by(date=day).all()


# ---------- reports ----------
@app.get("/students/{student_id}/attendance", response_model=schemas.StudentAttendanceReport)
def student_attendance(
    student_id: int,
    start: Optional[date] = Query(None, description="From date (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="To date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """One student's attendance records + summary, optionally within a date range."""
    student = get_student_or_404(db, student_id)
    q = db.query(models.Attendance).filter_by(student_id=student_id)
    if start:
        q = q.filter(models.Attendance.date >= start)
    if end:
        q = q.filter(models.Attendance.date <= end)
    records = q.order_by(models.Attendance.date).all()
    return schemas.StudentAttendanceReport(summary=build_summary(student, records), records=records)


@app.get("/students/roll/{roll_no}/attendance", response_model=schemas.StudentAttendanceReport)
def student_attendance_by_roll(roll_no: str, db: Session = Depends(get_db)):
    """Same report, looked up by roll number."""
    student = db.query(models.Student).filter_by(roll_no=roll_no).first()
    if not student:
        raise HTTPException(404, "Student not found")
    records = sorted(student.records, key=lambda r: r.date)
    return schemas.StudentAttendanceReport(summary=build_summary(student, records), records=records)


@app.get("/reports/summary", response_model=List[schemas.AttendanceSummary])
def all_students_summary(db: Session = Depends(get_db)):
    """Attendance percentage for every student."""
    return [build_summary(s, s.records) for s in db.query(models.Student).order_by(models.Student.roll_no)]


@app.get("/reports/low-attendance", response_model=List[schemas.AttendanceSummary])
def low_attendance(threshold: float = 75.0, db: Session = Depends(get_db)):
    """Students below the given percentage (default 75%)."""
    summaries = [build_summary(s, s.records) for s in db.query(models.Student).all()]
    return [s for s in summaries if s.total_days and s.percentage < threshold]
