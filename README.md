# Attendance Management System (FastAPI + SQLite)

## Setup
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://127.0.0.1:8000 for the web page (API docs are at /docs).
Data is saved in `attendance.db` (created automatically in this folder).

## Main endpoints
| Method | URL | What it does |
|---|---|---|
| POST | /students | Add student |
| GET | /students | List students |
| POST | /attendance | Mark attendance (status: present/absent/late) |
| PUT | /attendance/{id} | Edit a record |
| GET | /attendance/date/2026-10-28 | Everyone's attendance on a date |
| GET | /students/{id}/attendance | One student's records + summary (`?start=&end=`) |
| GET | /students/roll/{roll_no}/attendance | Same, by roll number |
| GET | /reports/summary | % for all students |
| GET | /reports/low-attendance?threshold=75 | Students below 75% |

## Sample data
POST /students  ->  {"roll_no": "CS201", "name": "Rahul", "course": "B.Tech CSE"}
POST /attendance -> {"student_id": 1, "date": "2026-10-28", "status": "present"}
