# pyschic_tribble/routes/__init__.py

from .users import users_router
from .events import events_router
from .timeslots import timeslots_router
from .calendar import calendar_router

__all__ = [
    "users_router",
    "events_router",
    "timeslots_router",
    "calendar_router",
]
