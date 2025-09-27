from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from icalendar import Calendar, Event
from src.psychic_tribble.dependencies import get_db, get_current_user
from src.psychic_tribble.crud.task import get_tasks_for_user

router = APIRouter(prefix="/v1/calendar", tags=["calendar"])

@router.get("/ics", summary="Export tasks as iCalendar feed")
async def export_ics(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    tasks = await get_tasks_for_user(db, user.id)
    cal = Calendar()
    cal.add("prodid", "-//Psychic-Tribble//")
    cal.add("version", "2.0")

    for t in tasks:
        ev = Event()
        ev.add("uid", f"{t.id}@psychic-tribble")
        ev.add("summary", t.title)
        if t.due_date:
            ev.add("dtstart", t.due_date)
        ev.add("description", t.description or "")
        ev.add("status", "CONFIRMED" if not t.completed else "CANCELLED")
        cal.add_component(ev)

    return Response(content=cal.to_ical(), media_type="text/calendar")


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
