"""
Enhanced CLI interface for Psychic-Tribble Calendar Tool

This module provides a comprehensive command-line interface for the calendar
parsing and management functionality, building upon the existing REPL prototype.
"""

# Note: CLI requires click and rich (optional) dependencies
# Install with: pip install click rich

try:
    from .main import main
    __all__ = ['main']
except ImportError:
    print("CLI dependencies not available. Install with: pip install click rich")
    __all__ = []