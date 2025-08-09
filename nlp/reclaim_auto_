
from fastapi import FastAPI, Request, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import requests
import random
import enum
from pydantic import BaseModel
from typing import List, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

app = FastAPI()
engine = create_engine('sqlite:///psychic_tribble.db')  # Update as needed
Base = declarative_base()
Session = sessionmaker(bind=engine)
DUCKLING_URL = "http://localhost:8000"  # Set via env var if needed

# Enums and Models
class Priority(enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    priority = Column(Enum(Priority), default=Priority.HIGH)
    total_duration = Column(Float, nullable=False)  # Hours
    due_date = Column(DateTime, nullable=False)
    start_date = Column(DateTime)
    min_duration = Column(Float, default=0.5)
    max_duration = Column(Float, default=2.0)
    status = Column(String(20), default="Pending")
    source = Column(String(20), default="manual")

class Habit(Base):
    __tablename__ = 'habits'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    frequency = Column(String(20), nullable=False)  # e.g., "daily", "weekly"
    ideal_time_start = Column(String(5))  # e.g., "12:00"
    ideal_time_end = Column(String(5))  # e.g., "14:00"
    min_duration = Column(Float, default=0.5)
    max_duration = Column(Float, default=1.0)
    keywords = Column(String(200))
    source = Column(String(20), default="manual")

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    is_locked = Column(Boolean, default=False)
    task_id = Column(Integer)
    habit_id = Column(Integer)
    source = Column(String(20), default="manual")

Base.metadata.create_all(engine)

# Pydantic Models for Request/Response
class NaturalLanguageInput(BaseModel):
    text: str

class NaturalLanguageOutput(BaseModel):
    title: str
    start: str
    end: str
    duration: float
    priority: str

class TaskInput(BaseModel):
    user_id: int
    title: str
    description: Optional[str]
    priority: str = "HIGH"
    total_duration: float
    due_date: str
    start_date: Optional[str]
    min_duration: float = 0.5
    max_duration: float = 2.0
    source: str = "manual"

class TaskOutput(BaseModel):
    task: dict
    event: Optional[dict]

class HabitInput(BaseModel):
    user_id: int
    title: str
    priority: str = "MEDIUM"
    frequency: str
    ideal_time_start: str = "09:00"
    ideal_time_end: str = "17:00"
    min_duration: float = 0.5
    max_duration: float = 1.0
    keywords: Optional[str]
    source: str = "manual"

class HabitOutput(BaseModel):
    habit: dict
    events: List[dict]

class ScheduleInput(BaseModel):
    user_id: int

class ScheduleOutput(BaseModel):
    events: List[dict]

# Google Calendar Sync (Stub)
def get_google_calendar_events(user_id: int, start_time: datetime, end_time: datetime) -> List[dict]:
    # Implement OAuth2 flow and fetch events
    # Placeholder: Return mock events
    return [{'start': datetime.now(), 'end': datetime.now() + timedelta(hours=1)}]

# Scheduling Logic
def find_available_slots(user_id: int, start_time: datetime, end_time: datetime, duration: float, existing_events: List[dict]) -> List[tuple]:
    slots = []
    current_time = start_time
    while current_time + timedelta(hours=duration) <= end_time:
        conflict = False
        slot_end = current_time + timedelta(hours=duration)
        for event in existing_events:
            event_start = datetime.fromisoformat(event['start'])
            event_end = datetime.fromisoformat(event['end'])
            if not (slot_end <= event_start or current_time >= event_end):
                conflict = True
                break
        if not conflict:
            slots.append((current_time, slot_end))
        current_time += timedelta(minutes=15)
    return slots

def schedule_task(task: Task, user_id: int) -> Optional[Event]:
    external_events = get_google_calendar_events(user_id, datetime.now(), task.due_date)
    session = Session()
    existing_events = session.query(Event).filter_by(user_id=user_id, is_locked=True).all()
    existing_events_list = [{'start': e.start.isoformat(), 'end': e.end.isoformat()} for e in existing_events]
    existing_events_list.extend(external_events)
    start_time = task.start_date or datetime.now()
    end_time = task.due_date
    duration = min(task.max_duration, task.total_duration)
    
    slots = find_available_slots(user_id, start_time, end_time, duration, existing_events_list)
    if not slots:
        return None
    
    slot = random.choice(slots)
    event = Event(
        user_id=user_id,
        title=task.title,
        description=task.description,
        start=slot[0],
        end=slot[1],
        priority=task.priority,
        task_id=task.id,
        source="task"
    )
    session.add(event)
    session.commit()
    session.close()
    return event

def schedule_habit(habit: Habit, user_id: int, start_date: datetime, end_date: datetime) -> List[Event]:
    events = []
    external_events = get_google_calendar_events(user_id, start_date, end_date)
    session = Session()
    existing_events = session.query(Event).filter_by(user_id=user_id, is_locked=True).all()
    existing_events_list = [{'start': e.start.isoformat(), 'end': e.end.isoformat()} for e in existing_events]
    existing_events_list.extend(external_events)
    
    current_date = start_date
    while current_date <= end_date:
        if habit.frequency == "daily":
            ideal_start = datetime.strptime(habit.ideal_time_start, "%H:%M")
            ideal_end = datetime.strptime(habit.ideal_time_end, "%H:%M")
            start_time = current_date.replace(hour=ideal_start.hour, minute=ideal_start.minute)
            end_time = current_date.replace(hour=ideal_end.hour, minute=ideal_end.minute)
            duration = random.uniform(habit.min_duration, habit.max_duration)
            slots = find_available_slots(user_id, start_time, end_time, duration, existing_events_list)
            if slots:
                slot = random.choice(slots)
                event = Event(
                    user_id=user_id,
                    title=habit.title,
                    start=slot[0],
                    end=slot[1],
                    priority=habit.priority,
                    habit_id=habit.id,
                    source="habit"
                )
                session.add(event)
                events.append(event)
        current_date += timedelta(days=1)
    session.commit()
    session.close()
    return events

# Endpoints
@app.post("/parse_natural_language", response_model=NaturalLanguageOutput)
async def parse_natural_language(input: NaturalLanguageInput):
    try:
        response = requests.post(
            f"{DUCKLING_URL}/parse",
            data={
                "locale": "en_US",
                "text": input.text,
                "timezone": "US/Pacific"
            }
        )
        response.raise_for_status()
        entities = response.json()
        time_entity = next((e for e in entities if e['dim'] in ['time', 'interval']), None)
        if time_entity:
            if time_entity['dim'] == 'time':
                start = time_entity['value']['value']
                end = datetime.fromisoformat(start) + timedelta(hours=1)
            else:
                start = time_entity['value']['from']
                end = time_entity['value']['to']
            duration = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() / 3600
            return NaturalLanguageOutput(
                title=input.text,
                start=start,
                end=end,
                duration=duration,
                priority="MEDIUM"
            )
        raise HTTPException(status_code=400, detail="No time entity found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duckling error: {str(e)}")

@app.post("/tasks", response_model=TaskOutput)
async def create_task(task_input: TaskInput):
    session = Session()
    task = Task(
        user_id=task_input.user_id,
        title=task_input.title,
        description=task_input.description,
        priority=Priority[task_input.priority],
        total_duration=task_input.total_duration,
        due_date=datetime.fromisoformat(task_input.due_date),
        start_date=datetime.fromisoformat(task_input.start_date) if task_input.start_date else None,
        min_duration=task_input.min_duration,
        max_duration=task_input.max_duration,
        source=task_input.source
    )
    session.add(task)
    session.commit()
    event = schedule_task(task, task.user_id)
    session.close()
    if event:
        return TaskOutput(task=task.__dict__, event=event.__dict__)
    raise HTTPException(status_code=400, detail="No available slots")

@app.post("/habits", response_model=HabitOutput)
async def create_habit(habit_input: HabitInput):
    session = Session()
    habit = Habit(
        user_id=habit_input.user_id,
        title=habit_input.title,
        priority=Priority[habit_input.priority],
        frequency=habit_input.frequency,
        ideal_time_start=habit_input.ideal_time_start,
        ideal_time_end=habit_input.ideal_time_end,
        min_duration=habit_input.min_duration,
        max_duration=habit_input.max_duration,
        keywords=habit_input.keywords,
        source=habit_input.source
    )
    session.add(habit)
    session.commit()
    events = schedule_habit(habit, habit_input.user_id, datetime.now(), datetime.now() + timedelta(days=7))
    session.close()
    return HabitOutput(habit=habit.__dict__, events=[e.__dict__ for e in events])

@app.post("/schedule", response_model=ScheduleOutput)
async def optimize_schedule(schedule_input: ScheduleInput):
    session = Session()
    tasks = session.query(Task).filter_by(user_id=schedule_input.user_id, status="Pending").all()
    habits = session.query(Habit).filter_by(user_id=schedule_input.user_id).all()
    scheduled_events = []
    
    for task in sorted(tasks, key=lambda t: (t.priority.value, t.due_date)):
        event = schedule_task(task, schedule_input.user_id)
        if event:
            scheduled_events.append(event)
    
    scheduled_events.extend(schedule_habit(habits[0], schedule_input.user_id, datetime.now(), datetime.now() + timedelta(days=7)) if habits else [])
    session.close()
    return ScheduleOutput(events=[e.__dict__ for e in scheduled_events])

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
