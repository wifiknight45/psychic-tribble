#Helper Functions 
from datetime import time

def parse_time(tstr: str) -> time:
    """Convert 'HH:MM' into a datetime.time object."""
    h, m = map(int, tstr.split(":"))
    return time(hour=h, minute=m)
