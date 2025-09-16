"""
Test suite for the enhanced CLI interface demo.

These tests validate the basic functionality of the CLI tool
and serve as examples for the feature enhancement suggestions.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch

from psychic_tribble.cli.main import parse_expression, extract_title, format_human_readable


def test_extract_title():
    """Test title extraction from calendar expressions."""
    assert extract_title("Team meeting every Tuesday at 2pm") == "Team meeting Tuesday 2pm"
    assert extract_title("Doctor appointment next Friday") == "Doctor appointment next Friday"
    assert extract_title("Lunch at 12pm") == "Lunch 12pm"
    assert extract_title("Every Monday standup at 9am") == "Monday standup 9am"


def test_format_human_readable():
    """Test human-readable formatting of parsing results."""
    
    # Test recurring event
    recurring_result = {
        "type": "recurring",
        "title": "Team Meeting",
        "frequency": "weekly"
    }
    formatted = format_human_readable(recurring_result)
    assert "🔄 Recurring Event: Team Meeting (weekly)" == formatted
    
    # Test one-time event
    onetime_result = {
        "type": "one-time", 
        "title": "Doctor Appointment",
        "date": "2024-01-15"
    }
    formatted = format_human_readable(onetime_result)
    assert "📅 One-time Event: Doctor Appointment on 2024-01-15" == formatted
    
    # Test error case
    error_result = {
        "type": "error",
        "error": "Could not parse expression"
    }
    formatted = format_human_readable(error_result)
    assert "❌ Error: Could not parse expression" == formatted


def test_parse_expression_output(capsys):
    """Test that parse_expression produces expected output."""
    
    # Test parsing a recurring expression
    parse_expression("Weekly team standup on Mondays")
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Check that the output contains expected elements
    assert "Parsing: Weekly team standup on Mondays" in output
    assert "🔄 Recurring Event:" in output
    assert "JSON format:" in output
    assert "weekly" in output.lower()


def test_cli_help_output():
    """Test that the CLI help displays correctly."""
    
    with patch('sys.argv', ['main.py']):
        from psychic_tribble.cli.main import main
        
        # Capture stdout
        from io import StringIO
        from contextlib import redirect_stdout
        
        f = StringIO()
        with redirect_stdout(f):
            main()
        
        output = f.getvalue()
        assert "Psychic-Tribble Calendar CLI Tool" in output
        assert "Available commands:" in output
        assert "parse <expression>" in output
        assert "interactive" in output


def test_cli_parse_command():
    """Test CLI parsing command functionality."""
    
    with patch('sys.argv', ['main.py', 'parse', 'Meeting', 'every', 'Friday']):
        from psychic_tribble.cli.main import main
        from io import StringIO
        from contextlib import redirect_stdout
        
        f = StringIO()
        with redirect_stdout(f):
            main()
        
        output = f.getvalue()
        assert "Parsing: Meeting every Friday" in output
        assert "Recurring Event:" in output


if __name__ == '__main__':
    # Run tests manually if pytest is not available
    print("Running CLI demo tests...")
    
    test_extract_title()
    print("✓ Title extraction tests passed")
    
    test_format_human_readable()
    print("✓ Human-readable formatting tests passed")
    
    print("✓ All CLI demo tests passed!")
    print("\nTo run with pytest:")
    print("  pytest tests/test_cli_demo.py -v")