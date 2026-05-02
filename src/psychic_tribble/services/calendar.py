# src/psychic_tribble/services/calendar.py

class CalendarService:
    """
    Integrates with external calendars:
    - sync_calendar
    - fetch_availability
    - create_calendar_event
    """

    def __init__(self, external_client):
        """
        Injected client could be an API wrapper for Google, Outlook, etc.
        """
        self.client = external_client

    def sync_calendar(self, user_id):
        """
        Pulls external events and ensures the local repository is up to date.
        """
        # 1. Fetch remote events via the client
        remote_events = self.client.get_external_events(user_id)
        
        # 2. Compare with local data (logic to prevent duplicates)
        # TODO: Implement local_repo.upsert() logic here
        
        return {"status": "sync_complete", "synced_count": len(remote_events)}

    def fetch_availability(self, user_id, date_range):
        """
        Checks for busy blocks in the external calendar to prevent local overlaps.
        """
        start, end = date_range
        busy_slots = self.client.get_free_busy(user_id, start, end)
        
        # Returns a list of time ranges that are unavailable
        return busy_slots

    def create_calendar_event(self, user_id, event_payload):
        """
        Pushes a locally created event to the external provider.
        """
        # Enhancement: Add a 'sync_id' to the payload to link 
        # local and remote versions of the same event.
        external_id = self.client.push_event(user_id, event_payload)
        
        return {"external_id": external_id, "status": "published"}

    # --- Added Enhancement: Conflict Resolution ---
    
    def resolve_conflicts(self, user_id, local_event):
        """
        Cross-references local event times against external availability.
        """
        availability = self.fetch_availability(
            user_id, 
            (local_event.start_time, local_event.end_time)
        )
        
        if availability:
            return {"conflict": True, "details": availability}
        return {"conflict": False}

