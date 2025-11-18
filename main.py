import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body, Query
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Level, Section, TimetableEntry, Announcement, Material, RoomBooking, Attendance, IDResponse

app = FastAPI(title="EE Department Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "EE Department Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:15]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Helpers

def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

# Admin endpoints

@app.post("/auth/register", response_model=IDResponse)
async def register_user(user: User):
    # Ensure unique email
    if db["user"].find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_dict = user.model_dump()
    inserted_id = create_document("user", user_dict)
    return {"id": inserted_id}

@app.get("/users", response_model=List[dict])
async def list_users(role: Optional[str] = Query(None), approved: Optional[bool] = Query(None)):
    filt = {}
    if role:
        filt["role"] = role
    if approved is not None:
        filt["approved"] = approved
    return get_documents("user", filt)

@app.patch("/users/{user_id}/approve")
async def approve_user(user_id: str, approved: bool = Body(True)):
    res = db["user"].update_one({"_id": _oid(user_id)}, {"$set": {"approved": approved}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}

# Levels & Sections
@app.post("/levels", response_model=IDResponse)
async def create_level(level: Level):
    return {"id": create_document("level", level)}

@app.get("/levels")
async def list_levels():
    return get_documents("level")

@app.post("/sections", response_model=IDResponse)
async def create_section(section: Section):
    # ensure level exists
    if not db["level"].find_one({"_id": _oid(section.level_id)}):
        raise HTTPException(status_code=400, detail="Level not found")
    return {"id": create_document("section", section)}

@app.get("/sections")
async def list_sections(level_id: Optional[str] = Query(None)):
    filt = {"level_id": level_id} if level_id else {}
    return get_documents("section", filt)

# Assign student to section
@app.patch("/users/{user_id}/section")
async def assign_section(user_id: str, section_id: str = Body(..., embed=True)):
    if not db["section"].find_one({"_id": _oid(section_id)}):
        raise HTTPException(status_code=400, detail="Section not found")
    res = db["user"].update_one({"_id": _oid(user_id)}, {"$set": {"section_id": section_id}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}

# Timetables
@app.post("/timetable", response_model=IDResponse)
async def add_timetable(entry: TimetableEntry):
    # Validate section
    if not db["section"].find_one({"_id": _oid(entry.section_id)}):
        raise HTTPException(status_code=400, detail="Section not found")
    return {"id": create_document("timetableentry", entry)}

@app.get("/timetable")
async def get_timetable(section_id: str):
    return get_documents("timetableentry", {"section_id": section_id})

# Announcements
@app.post("/announcements", response_model=IDResponse)
async def create_announcement(ann: Announcement):
    return {"id": create_document("announcement", ann)}

@app.get("/announcements")
async def list_announcements(audience: Optional[str] = Query(None), level_id: Optional[str] = Query(None), section_id: Optional[str] = Query(None)):
    filt = {}
    if audience: filt["audience"] = audience
    if level_id: filt["level_id"] = level_id
    if section_id: filt["section_id"] = section_id
    return get_documents("announcement", filt)

# Materials
@app.post("/materials", response_model=IDResponse)
async def upload_material(mat: Material):
    # For MVP: we store a URL to a file (pdf/image)
    return {"id": create_document("material", mat)}

@app.get("/materials")
async def list_materials(section_id: Optional[str] = Query(None), teacher_id: Optional[str] = Query(None)):
    filt = {}
    if section_id: filt["section_id"] = section_id
    if teacher_id: filt["teacher_id"] = teacher_id
    return get_documents("material", filt)

# Room booking
@app.post("/bookings", response_model=IDResponse)
async def request_booking(rb: RoomBooking):
    return {"id": create_document("roombooking", rb)}

@app.patch("/bookings/{booking_id}/status")
async def set_booking_status(booking_id: str, status_value: str = Body(..., embed=True)):
    if status_value not in ["pending", "approved", "declined"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    res = db["roombooking"].update_one({"_id": _oid(booking_id)}, {"$set": {"status": status_value}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"status": "ok"}

@app.get("/bookings")
async def list_bookings(status: Optional[str] = Query(None)):
    filt = {"status": status} if status else {}
    return get_documents("roombooking", filt)

# Attendance
@app.post("/attendance", response_model=IDResponse)
async def mark_attendance(a: Attendance):
    # basic presence record
    return {"id": create_document("attendance", a)}

@app.get("/attendance")
async def list_attendance(section_id: Optional[str] = Query(None), student_id: Optional[str] = Query(None), date: Optional[str] = Query(None)):
    filt = {}
    if section_id: filt["section_id"] = section_id
    if student_id: filt["student_id"] = student_id
    if date: filt["date"] = date
    return get_documents("attendance", filt)

# Schema exposure for the database viewer (optional utility)
@app.get("/schema")
async def get_schema_definitions():
    return {
        "user": User.model_json_schema(),
        "level": Level.model_json_schema(),
        "section": Section.model_json_schema(),
        "timetableentry": TimetableEntry.model_json_schema(),
        "announcement": Announcement.model_json_schema(),
        "material": Material.model_json_schema(),
        "roombooking": RoomBooking.model_json_schema(),
        "attendance": Attendance.model_json_schema(),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
