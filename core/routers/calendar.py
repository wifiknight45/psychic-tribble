

from datetime import datetime
import pytz
from icalendar import Calendar as iCalCalendar, Event as iCalEvent

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..auth import get_current_user
from ..db.models import Event

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get("/feed.ics", response_class=Response, summary="RFC 5545 iCalendar feed")
async def ics_feed(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    cal = iCalCalendar()
    cal.add("prodid", "-//Psychic Tribble//EN")
    cal.add("version", "2.0")

    events = db.query(Event).filter(Event.user_id == current_user.id).all()
    utc = pytz.UTC

    for ev in events:
        comp = iCalEvent()
        comp.add("uid", f"{ev.id}@psychic-tribble")
        comp.add("dtstamp", datetime.utcnow().replace(tzinfo=utc))
        comp.add("dtstart", ev.start_time.astimezone(utc))
        comp.add("dtend", ev.end_time.astimezone(utc))
        comp.add("summary", ev.title)
        if ev.description:
            comp.add("description", ev.description)
        if ev.location:
            comp.add("location", ev.location)
        cal.add_component(comp)

    return Response(content=cal.to_ical(), media_type="text/calendar; charset=utf-8")
