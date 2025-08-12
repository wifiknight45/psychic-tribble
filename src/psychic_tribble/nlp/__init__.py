"""
NLP Parser Module for Calendar Applications

This module provides natural language processing capabilities for parsing
calendar-related text inputs into structured data that can be converted
to calendar events and recurrence rules.

Main Components:
- CalendarNLPParser: Main parsing class with cascading approach
- HeuristicParser: Fast regex-based parsing for common patterns  
- LLMParser: LLM-based parsing for complex inputs
- Training utilities and data structures

Usage:
    from nlp import CalendarNLPParser
    
    parser = CalendarNLPParser()
    result = parser.parse("Team meeting every Tuesday at 2pm")
"""

from .parser import CalendarNLPParser
from .heuristics import HeuristicParser

# Import LLM parser conditionally in case dependencies aren't installed
try:
    from .llm_prompts import LLMParser
    __all__ = ['CalendarNLPParser', 'HeuristicParser', 'LLMParser']
except ImportError:
    # Graceful degradation if LLM dependencies not available
    LLMParser = None
    __all__ = ['CalendarNLPParser', 'HeuristicParser']

# Version info
__version__ = '0.1.0'
__author__ = 'Your Name'

# Default configuration
DEFAULT_CONFIG = {
    'heuristic_confidence_threshold': 0.8,
    'enable_llm_fallback': True,
    'llm_model': 'gpt-4o-mini',  # or 'ollama/llama3.2:3b'
    'cache_results': True,
    'max_cache_size': 1000
}

# Convenience function for quick parsing
def quick_parse(text: str, config: dict = None):
    """
    Quick parsing function for simple use cases
    
    Args:
        text: Natural language text to parse
        config: Optional configuration overrides
        
    Returns:
        dict: Parsed calendar event data
    """
    parser = CalendarNLPParser(config or DEFAULT_CONFIG)
    return parser.parse(text)

# Export commonly used patterns for external use
COMMON_PATTERNS = {
    'every_weekday': r'every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
    'every_nth_weekday': r'every\s+(\w+)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
    'ordinal_weekday': r'(first|second|third|fourth|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
    'time_12h': r'(\d{1,2}):?(\d{2})?\s*(am|pm)',
    'time_24h': r'(\d{1,2}):(\d{2})',
    'date_patterns': [
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',
        r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
        r'(\d{1,2})-(\d{1,2})-(\d{2,4})'
    ]
}

# Exception classes
class ParseError(Exception):
    """Base exception for parsing errors"""
    pass

class AmbiguousInputError(ParseError):
    """Raised when input is ambiguous and needs clarification"""
    def __init__(self, message, suggestions=None):
        super().__init__(message)
        self.suggestions = suggestions or []

class UnsupportedPatternError(ParseError):
    """Raised when input pattern is not supported"""
    pass

# Logging setup
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
