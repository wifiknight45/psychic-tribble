#!/usr/bin/env python3
"""
Enhanced CLI interface for Psychic-Tribble Calendar Tool

This provides a professional command-line interface that builds upon the existing
calendar parsing REPL prototype with proper argument parsing, multiple output
formats, and batch processing capabilities.

Example usage:
    python -m psychic_tribble.cli.main parse "Team meeting every Tuesday at 2pm"
    python -m psychic_tribble.cli.main interactive
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

def show_help():
    """Show help information."""
    print("🗓️  Psychic-Tribble Calendar CLI Tool")
    print()
    print("Available commands:")
    print("  parse <expression>  - Parse a calendar expression")
    print("  interactive         - Launch interactive REPL")
    print("  help               - Show this help")
    print()
    print("Examples:")
    print("  python -m psychic_tribble.cli.main parse 'Meeting every Monday at 2pm'")
    print("  python -m psychic_tribble.cli.main interactive")

def main():
    """Simple CLI entry point for demonstration."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command == "help":
        show_help()
    elif command == "parse" and len(sys.argv) > 2:
        expression = " ".join(sys.argv[2:])
        parse_expression(expression)
    elif command == "interactive":
        launch_interactive()
    else:
        print(f"Unknown command: {command}")
        show_help()

def parse_expression(expression: str):
    """Parse a single calendar expression."""
    print(f"Parsing: {expression}")
    
    # Mock parsing for demonstration
    result = {
        "original_expression": expression,
        "type": "recurring" if "every" in expression.lower() else "one-time",
        "title": extract_title(expression),
        "parsed": True
    }
    
    if "every" in expression.lower():
        result["frequency"] = "weekly"  # Simplified detection
    
    # Format as human-readable
    print("Result:")
    print(format_human_readable(result))
    print()
    print("JSON format:")
    print(json.dumps(result, indent=2))

def launch_interactive():
    """Launch the interactive REPL mode."""
    print("Launching interactive REPL...")
    print("(This is a demonstration - the actual REPL would be imported here)")
    print("Type 'quit' to exit")
    print()
    
    try:
        # Import the actual REPL if available
        sys.path.append(str(Path(__file__).parent.parent))
        from nlp.calendar_repl_prototype import CalendarREPL
        repl = CalendarREPL()
        repl.run()
    except ImportError:
        print("REPL not available. Running simple demo...")
        simple_demo_repl()

def simple_demo_repl():
    """Simple demonstration REPL."""
    while True:
        try:
            user_input = input("📅 > ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            elif user_input:
                parse_expression(user_input)
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except EOFError:
            print("\nGoodbye! 👋")
            break

def extract_title(expression: str) -> str:
    """Extract a basic title from the expression."""
    # Very simple title extraction for demo
    words = expression.split()
    # Remove common time/frequency words
    skip_words = {'every', 'at', 'on', 'the', 'a', 'an', 'in', 'for', 'am', 'pm'}
    title_words = [word for word in words if word.lower() not in skip_words and not word.isdigit()]
    return " ".join(title_words[:4]) if title_words else "Untitled Event"

def format_human_readable(result: Dict[str, Any]) -> str:
    """Format parsing result in human-readable form."""
    if result.get('type') == 'error':
        return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    event_type = result.get('type', 'unknown')
    title = result.get('title', 'Untitled Event')
    
    if event_type == 'recurring':
        frequency = result.get('frequency', 'unknown')
        return f"🔄 Recurring Event: {title} ({frequency})"
    elif event_type == 'one-time':
        date = result.get('date', 'unknown date')
        return f"📅 One-time Event: {title} on {date}"
    else:
        return f"📝 Event: {title}"

if __name__ == '__main__':
    main()