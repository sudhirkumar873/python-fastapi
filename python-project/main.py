from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class RatingResponse(BaseModel):
    message: str

app = FastAPI()

# Connect to MongoDB
client = AsyncIOMotorClient('mongodb://localhost:27017/')
db = client['kimo_courses_db']
courses_collection = db['courses']

# Pydantic models
class Chapter(BaseModel):
    name: str
    text: str
    ratings: Optional[dict] = Field(default_factory=lambda: {"positive": 0, "negative": 0})

class Course(BaseModel):
    name: str
    date: datetime
    description: str
    domain: List[str]
    chapters: List[Chapter]

# Endpoints

@app.get("/courses/", response_model=List[Course])
async def get_courses(sort: str = Query("alphabetical", regex="^(alphabetical|date|rating)$"), domain: Optional[str] = None):
    sort_fields = {
        "alphabetical": ("name", 1),  # 1 for ASCENDING
        "date": ("date", -1),         # -1 for DESCENDING
        "rating": ("chapters.ratings.positive", -1)  # Assuming rating is pre-calculated and stored
    }
    sort_field, order = sort_fields[sort]

    filter_query = {"domain": domain} if domain else {}

    courses = await courses_collection.find(filter_query).sort(sort_field, order).to_list(None)
    return courses

@app.get("/courses/{course_id}/", response_model=Course)
async def get_course_overview(course_id: str):
    course = await courses_collection.find_one({"_id": course_id})
    if course:
        return course
    raise HTTPException(status_code=404, detail="Course not found")

# Endpoint to get all chapters of a specific course
@app.get("/courses/{course_id}/chapters/", response_model=List[Chapter])
async def get_all_chapters(course_id: str):
    course = await courses_collection.find_one({"_id": course_id})
    if course:
        return course["chapters"]
    raise HTTPException(status_code=404, detail="Course not found")

@app.get("/courses/{course_id}/chapters/{chapter_id}/", response_model=Chapter)
async def get_chapter_info(course_id: str, chapter_id: str):
    # Find the course by its ID
    course = await courses_collection.find_one({"_id": course_id})
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Search for the chapter by its ID within the chapters list
    chapter = next((chap for chap in course["chapters"] if chap["_id"] == chapter_id), None)

    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Return the chapter, ensuring it's validated against the Chapter model
    return Chapter(**chapter)

@app.post("/courses/{course_id}/chapters/{chapter_id}/rate/", response_model=RatingResponse)
async def rate_chapter(course_id: str, chapter_id: str, positive: bool):
    # Find the course by its ID
    course = await courses_collection.find_one({"_id": course_id})
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Find the chapter by its ID within the chapters list
    for chapter in course["chapters"]:
        if chapter["_id"] == chapter_id:
            rating_type = "positive" if positive else "negative"
            
            # If the ratings field does not exist, initialize it
            if "ratings" not in chapter:
                chapter["ratings"] = {"positive": 0, "negative": 0}
            
            # Increment the appropriate rating
            chapter["ratings"][rating_type] += 1
            
            # Update the course document in MongoDB
            await courses_collection.update_one(
                {"_id": course_id, "chapters._id": chapter_id},
                {"$set": {"chapters.$.ratings": chapter["ratings"]}}
            )
            
            return RatingResponse(message="Rating updated successfully")

    raise HTTPException(status_code=404, detail="Chapter not found")