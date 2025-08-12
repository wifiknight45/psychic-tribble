from dataclasses import dataclass, field
from datetime import time
from typing import Dict

@dataclass
class User:
    user_id: str
    name: str

@dataclass
class Timeslot:
    ts_id: str
    day: str
    start: time
    end: time
    assigned_user_ids: set = field(default_factory=set)

@dataclass
class Event:
    event_id: str
    name: str
    timeslots: Dict[str, Timeslot] = field(default_factory=dict)
