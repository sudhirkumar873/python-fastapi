import json
from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['kimo_courses_db']
courses_collection = db['courses']

# Create indices
courses_collection.create_index([('name', ASCENDING)], unique=True)
courses_collection.create_index([('date', DESCENDING)])
courses_collection.create_index([('domain', ASCENDING)])

# Load data from courses.json
with open('courses.json', encoding='utf-8') as f:
    courses = json.load(f)

# Convert UNIX timestamps to datetime objects
for course in courses:
    course['date'] = datetime.fromtimestamp(course['date'])

# Convert _id fields to strings
for course in courses:
    course['_id'] = str(course['_id'])
    for chapter in course.get('chapters', []):
        chapter['_id'] = str(chapter['_id'])

# Prepare bulk write operations
operations = []
for course in courses:
    operations.append(
        UpdateOne(
            {'name': course['name']},  # Filter to find existing document
            {'$set': course},          # Update fields or insert if not found
            upsert=True                # Create if not found
        )
    )

# Execute bulk write
result = courses_collection.bulk_write(operations)

print("Courses loaded into MongoDB successfully.")
print(f"Inserted: {result.upserted_count}")
print(f"Modified: {result.modified_count}")
print(f"Matched: {result.matched_count}")
