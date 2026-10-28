from datetime import date
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class Status(str, Enum):
    present = "present"
    absent = "absent"
    late = "late"


class StudentCreate(BaseModel):
    roll_no: str
    name: str
    email: Optional[str] = None
    course: Optional[str] = None


class StudentOut(StudentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: Status
    remark: Optional[str] = None


class AttendanceUpdate(BaseModel):
    status: Status
    remark: Optional[str] = None


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    date: date
    status: str
    remark: Optional[str] = None


class AttendanceSummary(BaseModel):
    student_id: int
    roll_no: str
    name: str
    total_days: int
    present: int
    late: int
    absent: int
    percentage: float


class StudentAttendanceReport(BaseModel):
    summary: AttendanceSummary
    records: List[AttendanceOut]
