"""
Database Schemas for Electrical Engineering Department Management

Each Pydantic model maps to a MongoDB collection (lowercased class name).
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# Core user schema
class User(BaseModel):
    full_name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email (unique)")
    password: str = Field(..., description="Hashed password or placeholder for MVP")
    role: Literal["admin", "teacher", "student"] = Field(..., description="User role")
    approved: bool = Field(False, description="Whether the account is approved by admins")
    section_id: Optional[str] = Field(None, description="For students: section they belong to")

# Academic level (e.g., 1ere annee licence, 2eme annee, Master, etc.)
class Level(BaseModel):
    name: str = Field(..., description="Level display name")
    description: Optional[str] = Field(None, description="Optional description")

# Section inside a level (e.g., A, B, C)
class Section(BaseModel):
    level_id: str = Field(..., description="Reference to level _id as string")
    name: str = Field(..., description="Section name, e.g., A, B, C")

# Timetable entry for a section
class TimetableEntry(BaseModel):
    section_id: str = Field(..., description="Section id")
    day: Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    start_time: str = Field(..., description="Start time HH:MM")
    end_time: str = Field(..., description="End time HH:MM")
    room: str = Field(..., description="Room name/number")
    subject: str = Field(..., description="Course/subject name")
    teacher_id: Optional[str] = Field(None, description="Teacher responsible")

# Announcement/Notification
class Announcement(BaseModel):
    title: str
    body: str
    author_id: Optional[str] = None
    audience: Literal["all", "admins", "teachers", "students", "level", "section"] = "all"
    level_id: Optional[str] = None
    section_id: Optional[str] = None
    pinned: bool = False

# Teacher material (link-based for MVP)
class Material(BaseModel):
    teacher_id: str
    section_id: Optional[str] = None
    title: str
    url: str = Field(..., description="Public URL to PDF/image/drive link")
    description: Optional[str] = None

# Room booking request
class RoomBooking(BaseModel):
    room: str
    date: str = Field(..., description="YYYY-MM-DD")
    start_time: str
    end_time: str
    purpose: Optional[str] = None
    requested_by: str = Field(..., description="Teacher user id")
    status: Literal["pending", "approved", "declined"] = "pending"

# Attendance record
class Attendance(BaseModel):
    section_id: str
    timetable_id: Optional[str] = None
    date: str = Field(..., description="YYYY-MM-DD")
    student_id: str
    present: bool = True

# Utility response models (optional minimal)
class IDResponse(BaseModel):
    id: str

class Paginated(BaseModel):
    total: int
    items: list
