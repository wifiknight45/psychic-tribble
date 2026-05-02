# src/psychic_tribble/services/service.py
from datetime import datetime

class TimeslotService:
    """
    Manages timeslot allocation and validation:
    - create_timeslot
    - get_timeslots_for_event
    - update_timeslot
    - delete_timeslot
    """

    def __init__(self, repository):
        self.repository = repository

    def create_timeslot(self, event_id, timeslot_data):
        """
        Allocates time for an event, ensuring no overlaps exist.
        """
        start = timeslot_data.get("start_time")
        end = timeslot_data.get("end_time")

        # Business Rule: Prevent double-booking
        if self._has_overlap(start, end):
            raise ValueError("This timeslot overlaps with an existing appointment.")

        timeslot_data["event_id"] = event_id
        return self.repository.add(timeslot_data)

    def get_timeslots_for_event(self, event_id):
        """
        Retrieves all time blocks associated with a specific task/event.
        """
        return self.repository.find_by_criteria({"event_id": event_id})

    def update_timeslot(self, timeslot_id, updates):
        """
        Modifies a specific time block.
        """
        if "start_time" in updates or "end_time" in updates:
            # Re-check for overlaps if the time is changing
            new_start = updates.get("start_time")
            new_end = updates.get("end_time")
            if self._has_overlap(new_start, new_end, ignore_id=timeslot_id):
                raise ValueError("Updated time conflicts with another slot.")

        return self.repository.update(timeslot_id, updates)

    def delete_timeslot(self, timeslot_id):
        """
        Removes a specific allocation of time.
        """
        return self.repository.delete(timeslot_id)

    def _has_overlap(self, start, end, ignore_id=None):
        """
        Internal helper to check if a time range is already taken.
        """
        all_slots = self.repository.get_all()
        for slot in all_slots:
            if ignore_id and slot.id == ignore_id:
                continue
            # Logic: (StartA < EndB) and (EndA > StartB)
            if start < slot.end_time and end > slot.start_time:
                return True
        return False
