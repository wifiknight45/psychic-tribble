import pytest
from datetime import datetime, timedelta
from psychic_tribble.core.utils import parse_iso_datetime, validate_time_range

def test_parse_iso_datetime_success():
    iso_str = "2025-08-02T12:34:56"
    dt = parse_iso_datetime(iso_str)
    assert isinstance(dt, datetime)
    assert dt.isoformat() == iso_str

def test_parse_iso_datetime_invalid_format_raises():
    with pytest.raises(ValueError):
        parse_iso_datetime("not-a-valid-date")

def test_validate_time_range_validates_correctly():
    start = datetime.utcnow()
    end = start + timedelta(hours=2)
    # Should not raise for a valid range
    validate_time_range(start, end)

def test_validate_time_range_end_before_start_raises():
    start = datetime.utcnow()
    end = start - timedelta(minutes=30)
    with pytest.raises(ValueError):
        validate_time_range(start, end)
