# src/psychic_tribble/services/__init__.py

import logging
from .user_service import UserService
from .event_service import EventService
from .timeslot_service import TimeslotService
from .calendar_service import CalendarService

# Set up package-level logging for robust error tracking
logger = logging.getLogger(__name__)

__all__ = [
    "UserService",
    "EventService",
    "TimeslotService",
    "CalendarService",
    "initialize_services",
]

def initialize_services(repository, external_client=None):
    """
    Helper function to initialize all services at once.
    Ensures that if one service fails to load, it's caught gracefully.
    """
    try:
        user_service = UserService(repository)
        event_service = EventService(repository)
        timeslot_service = TimeslotService(repository)
        calendar_service = CalendarService(external_client)
        
        logger.info("All services initialized successfully.")
        
        return {
            "user": user_service,
            "event": event_service,
            "timeslot": timeslot_service,
            "calendar": calendar_service
        }
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise RuntimeError("Core logic initialization failed. Check repository configuration.") from e
