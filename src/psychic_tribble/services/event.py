# src/psychic_tribble/services/event.py
from datetime import datetime

class EventService:
    """
    Handles event CRUD and business rules:
    - create_event
    - list_events
    - update_event
    - cancel_event
    """

    def __init__(self, repository):
        self.repository = repository

    def create_event(self, event_payload: dict):
        """
        Validates the payload and persists a new event via the repository.
        """
        # Basic validation: Ensure required fields exist
        required_fields = ["title", "start_time"]
        if not all(k in event_payload for k in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")

        # Business Rule: Ensure start_time is a datetime object or valid ISO string
        if isinstance(event_payload["start_time"], str):
            event_payload["start_time"] = datetime.fromisoformat(event_payload["start_time"])

        return self.repository.add(event_payload)

    def list_events(self, filters=None):
        """
        Retrieves events, optionally filtered by status or date range.
        """
        # If no filters, get everything from the repository
        events = self.repository.get_all()
        
        if filters:
            # Simple filtering logic example (e.g., filter by title or date)
            return [e for e in events if all(getattr(e, k, None) == v for k, v in filters.items())]
        
        return events

    def update_event(self, event_id: str, changes: dict):
        """
        Updates an existing event's attributes while preserving its ID.
        """
        event = self.repository.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event with ID {event_id} not found.")

        # Prevent ID from being changed
        changes.pop("id", None)
        
        return self.repository.update(event_id, changes)

    def cancel_event(self, event_id: str):
        """
        Soft-deletes or cancels an event. 
        """
        # Instead of a hard delete, we update a 'status' flag 
        # which is better for data analytics later.
        return self.repository.update(event_id, {"status": "cancelled"})

