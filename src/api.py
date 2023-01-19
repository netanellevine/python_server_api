from typing import Union
from fastapi import FastAPI
from data import data as dt
from pydantic import BaseModel, validator
from datetime import datetime
from enum import Enum

class Instructor(BaseModel):
    userId: str
    firstName: str
    lastName: str
    phoneNumber: str
    workPlace: str

class Participant(BaseModel):
    userId: str
    firstName: str
    lastName: str
    phoneNumber: str

class LessonLevel(str, Enum):
    All = "All"
    A = "A"
    B = "B"
    C = "C"


# key -> dd/mm/YYYY_HH:MM-HH:MM # date and start and end time
# lesson -> { 
#     "ParticipantsList": list[str],
#     "description": str,
#     "lessonName": str,
#     "level": str,
#     "maxNumberOfParticipants": int,
#     "price": float,
# }

class Search(BaseModel):
    instructorName: str
    lessonName: str
    level: list[str]
    price: int
    date: str


class Lesson(BaseModel):
    ParticipantsList: list[str]
    description: str = ""
    lessonName: str
    level: str
    maxNumberOfParticipants: int
    price: float

class LessonDocument(BaseModel):
    key: str
    lesson: Lesson

app = FastAPI()


# @app.get("/")
# def root():
#     return {"Hello": "World"}

# POST: to create data.
# GET: to read data.
# PUT: to update data.
# DELETE: to delete data.

# def instructor_exists(self, user_id) -> bool: GET
# def create_instructor(self, user_id, first_name, last_name, work_place) -> None: POST
# def participant_exists(self, user_id) -> bool: GET
# def add_participant(self, user_id, first_name, last_name) -> None: POST
# def getInstructorTimeFromDatabase(self, user_id) -> dict: GET
# def addUserToLesson(self, userId, key, lesson, userToAdd) -> None: POST
# def removeUserFromLesson(self, userId, key, lesson, userToAdd) -> None: DELETE
# def validateLesson(self, userId, key, lesson_to_add) -> bool: GET
# def getAvailability(self,userId ,date): GET


dal = dt(True)

@app.get("/instructor/exists")
def instructor_exists(userId: str) -> bool:
    return dal.instructor_exists(userId)

@app.post("/instructor/create")
def create_instructor(instructor: Instructor) -> bool:
    return dal.create_instructor(instructor)

@app.get("/participant/exists")
def participant_exists(userId: str) -> bool:
    return dal.participant_exists(userId)

@app.post("/participant/create")
def create_participant(participant: Participant) -> bool:
    return dal.create_participant(participant)

@app.get("/instructor/date")
def get_instructor_lessons_by_date(userId: str, date: str) -> list:
    return dal.get_instructor_lessons_by_date(userId, date)

@app.post("/instructor/addLesson")
def add_lesson(userId: str, key: str, lesson_to_add: Lesson) -> bool:
    return dal.validate_and_add_lesson(userId, key, lesson_to_add.dict())

@app.post("/lesson/addUser")
def add_participant_to_lesson(userId: str, key: str, lesson: Lesson, userToAdd: str) -> None:
    return dal.add_participant_to_lesson(userId, key, lesson.dict(), userToAdd)

@app.post("/lesson/removeUser")
def remove_participant_from_lesson(userId: str, key: str, lesson: Lesson, userToAdd: str) -> None:
    return dal.remove_participant_from_lesson(userId, key, lesson.dict(), userToAdd)

@app.get("/lesson/availability")
def get_availability(userId: str, date: str) -> list:
    return dal.get_availability(userId, date)

@app.get("/instructor/phone")
def get_instructor_phone(instructor_id: str) -> str:
    return dal.get_instructor_phone(instructor_id)

@app.get("/participant/phone")
def get_participant_phone(participant_id: str) -> str:
    return dal.get_participant_phone(participant_id)

@app.get("/instructor/name")
def get_instructor_name(instructor_id: str) -> str:
    return dal.get_instructor_name(instructor_id)

@app.get("/instructor/id")
def get_instructor_id(instructor_name: str) -> str:
    return dal.get_instructor_id(instructor_name)

@app.post("/lessons/search")
def get_lessons_by_search(search: Search) -> list:
    return dal.get_lessons_by_search(search.dict())


@app.get("/instructor/stats")
def get_instructor_name(userId: str,startDate: str , endDate:str) -> dict:
    return dal.get_instructor_stat(userId,startDate,endDate)

@app.get('/lessons/delete')
def delete_lesson(instructor_id: str, full_date: str) -> bool:
    return dal.delete_lesson(instructor_id, full_date)

@app.get('/lessons/upcoming')
def upcoming_lessons(userId: str,startDate: str,upcomingAmount:int) -> list:
    return dal.upcoming_lessons(userId,startDate,upcomingAmount)

@app.get('/lessons/history')
def history_lessons(userId: str,endDate: str,historyAmount:int) -> list:
    return dal.history_lessons(userId,endDate,historyAmount)


@app.get('/lessons/participant/upcoming')
def upcoming_participant_lessons(userId: str,startDate: str,upcomingAmount:int) -> list:
    return dal.upcoming_participant_lessons(userId,startDate,upcomingAmount)

@app.get('/lessons/participant/history')
def history_participant_lessons(userId: str,endDate: str,historyAmount:int) -> list:
    return dal.history_participant_lessons(userId,endDate,historyAmount)
