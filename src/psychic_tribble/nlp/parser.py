"""
Calendar NLP Parser with comprehensive regex patterns and training data
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ParseResult:
    """Container for parsing results with confidence scoring"""
    data: Dict[str, Any]
    confidence: float
    method: str  # 'heuristic', 'nlp', 'llm'
    raw_matches: Dict[str, Any] = None
    suggestions: List[str] = None

class RegexPatterns:
    """Comprehensive regex patterns for calendar parsing"""
    
    # Frequency patterns
    FREQUENCY_PATTERNS = {
        'daily': [
            r'\b(daily|every\s+day|each\s+day)\b',
            r'\bevery\s+(\d+)\s+days?\b',
        ],
        'weekly': [
            r'\b(weekly|every\s+week|each\s+week)\b',
            r'\bevery\s+(\d+)\s+weeks?\b',
        ],
        'monthly': [
            r'\b(monthly|every\s+month|each\s+month)\b',
            r'\bevery\s+(\d+)\s+months?\b',
        ],
        'yearly': [
            r'\b(yearly|annually|every\s+year|each\s+year)\b',
            r'\bevery\s+(\d+)\s+years?\b',
        ]
    }
    
    # Weekday patterns
    WEEKDAYS = {
        'monday': ['monday', 'mon', 'mondays'],
        'tuesday': ['tuesday', 'tue', 'tues', 'tuesdays'],
        'wednesday': ['wednesday', 'wed', 'wednesdays'],
        'thursday': ['thursday', 'thu', 'thur', 'thurs', 'thursdays'],
        'friday': ['friday', 'fri', 'fridays'],
        'saturday': ['saturday', 'sat', 'saturdays'],
        'sunday': ['sunday', 'sun', 'sundays']
    }
    
    WEEKDAY_PATTERN = r'\b(' + '|'.join([
        variant for variants in WEEKDAYS.values() for variant in variants
    ]) + r')\b'
    
    # Ordinal patterns
    ORDINALS = {
        'first': ['first', '1st'],
        'second': ['second', '2nd'],
        'third': ['third', '3rd'],
        'fourth': ['fourth', '4th'],
        'fifth': ['fifth', '5th'],
        'last': ['last', 'final']
    }
    
    ORDINAL_PATTERN = r'\b(' + '|'.join([
        variant for variants in ORDINALS.values() for variant in variants
    ]) + r')\b'
    
    # Time patterns
    TIME_PATTERNS = {
        '12_hour': [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2})\.(\d{2})\s*(am|pm)',
        ],
        '24_hour': [
            r'(\d{1,2}):(\d{2})(?!\s*(am|pm))',
            r'(\d{4})(?!\s*(am|pm))',  # 1430 format
        ],
        'relative': [
            r'\b(noon|midnight)\b',
            r'\b(morning|afternoon|evening|night)\b',
        ]
    }
    
    # Duration patterns
    DURATION_PATTERNS = [
        r'for\s+(\d+)\s+(hours?|hrs?|h)\b',
        r'for\s+(\d+)\s+(minutes?|mins?|m)\b',
        r'for\s+(\d+)\s+and\s+(\d+)\s+(hours?|hrs?)\s+(minutes?|mins?)\b',
        r'(\d+)\s+(hours?|hrs?|h)\s+long\b',
        r'(\d+)\s+(minutes?|mins?|m)\s+long\b',
    ]
    
    # Date patterns
    DATE_PATTERNS = {
        'relative': [
            r'\b(today|tomorrow|yesterday)\b',
            r'\bnext\s+(week|month|year)\b',
            r'\blast\s+(week|month|year)\b',
            r'\bthis\s+(week|month|year)\b',
            r'\bin\s+(\d+)\s+(days?|weeks?|months?|years?)\b',
        ],
        'absolute': [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b',
            r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',
            r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b',
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
        ]
    }
    
    # Complex recurring patterns
    RECURRING_PATTERNS = {
        'every_weekday': r'\bevery\s+(' + WEEKDAY_PATTERN.strip(r'\b()') + r')\b',
        'every_nth_weekday': r'\bevery\s+(\w+)\s+(' + WEEKDAY_PATTERN.strip(r'\b()') + r')\b',
        'ordinal_weekday': ORDINAL_PATTERN + r'\s+' + WEEKDAY_PATTERN,
        'weekdays_only': r'\b(weekdays?|business\s+days?|work\s+days?)\b',
        'weekends_only': r'\b(weekends?|saturday\s+and\s+sunday)\b',
        'multiple_weekdays': r'\b(' + WEEKDAY_PATTERN.strip(r'\b()') + r')\s+and\s+(' + WEEKDAY_PATTERN.strip(r'\b()') + r')\b',
    }

class TrainingData:
    """Comprehensive training examples for model training"""
    
    TRAINING_EXAMPLES = [
        # Simple recurring events
        {
            "input": "Team meeting every Tuesday at 2pm",
            "output": {
                "title": "Team meeting",
                "type": "recurring",
                "frequency": "weekly",
                "weekday": "tuesday",
                "start_time": "14:00",
                "confidence": 0.95
            }
        },
        {
            "input": "Daily standup at 9:30 AM",
            "output": {
                "title": "Daily standup",
                "type": "recurring",
                "frequency": "daily",
                "start_time": "09:30",
                "confidence": 0.95
            }
        },
        {
            "input": "Gym session every Monday and Wednesday at 6pm",
            "output": {
                "title": "Gym session",
                "type": "recurring",
                "frequency": "weekly",
                "weekdays": ["monday", "wednesday"],
                "start_time": "18:00",
                "confidence": 0.90
            }
        },
        {
            "input": "Monthly review meeting first Friday of every month at 10am",
            "output": {
                "title": "Monthly review meeting",
                "type": "recurring",
                "frequency": "monthly",
                "weekday": "friday",
                "ordinal": "first",
                "start_time": "10:00",
                "confidence": 0.85
            }
        },
        
        # Single events
        {
            "input": "Doctor appointment tomorrow at 3:30 PM",
            "output": {
                "title": "Doctor appointment",
                "type": "single",
                "relative_date": "tomorrow",
                "start_time": "15:30",
                "confidence": 0.90
            }
        },
        {
            "input": "Birthday party on March 15th at 7pm",
            "output": {
                "title": "Birthday party",
                "type": "single",
                "month": "march",
                "day": 15,
                "start_time": "19:00",
                "confidence": 0.90
            }
        },
        
        # Complex patterns
        {
            "input": "Weekly team sync every Thursday from 2-3pm",
            "output": {
                "title": "Weekly team sync",
                "type": "recurring",
                "frequency": "weekly",
                "weekday": "thursday",
                "start_time": "14:00",
                "end_time": "15:00",
                "confidence": 0.95
            }
        },
        {
            "input": "Workout session every other Monday for 1 hour starting at 6am",
            "output": {
                "title": "Workout session",
                "type": "recurring",
                "frequency": "weekly",
                "interval": 2,
                "weekday": "monday",
                "start_time": "06:00",
                "duration": "1h",
                "confidence": 0.85
            }
        },
        {
            "input": "Lunch meeting next Friday at noon in the conference room",
            "output": {
                "title": "Lunch meeting",
                "type": "single",
                "relative_date": "next friday",
                "start_time": "12:00",
                "location": "conference room",
                "confidence": 0.85
            }
        },
        
        # Duration-based events
        {
            "input": "Project planning session for 3 hours starting at 9am",
            "output": {
                "title": "Project planning session",
                "type": "single",
                "start_time": "09:00",
                "duration": "3h",
                "confidence": 0.85
            }
        },
        {
            "input": "Code review every Tuesday from 10:30 to 11:30",
            "output": {
                "title": "Code review",
                "type": "recurring",
                "frequency": "weekly",
                "weekday": "tuesday",
                "start_time": "10:30",
                "end_time": "11:30",
                "confidence": 0.90
            }
        },
        
        # Business day patterns
        {
            "input": "Daily check-in weekdays at 8:30am",
            "output": {
                "title": "Daily check-in",
                "type": "recurring",
                "frequency": "daily",
                "weekdays_only": True,
                "start_time": "08:30",
                "confidence": 0.90
            }
        },
        
        # Edge cases and ambiguous inputs
        {
            "input": "Meeting Tuesday",
            "output": {
                "title": "Meeting",
                "type": "single",
                "weekday": "tuesday",
                "ambiguous": ["this tuesday", "next tuesday"],
                "confidence": 0.40
            }
        },
        {
            "input": "Call at 2",
            "output": {
                "title": "Call",
                "type": "single",
                "start_time": "14:00",  # Assume 2pm
                "ambiguous": ["2am", "2pm"],
                "confidence": 0.50
            }
        }
    ]
    
    # Negative examples (should not parse successfully)
    NEGATIVE_EXAMPLES = [
        "This is just a random sentence",
        "I like pizza",
        "The weather is nice today",
        "How are you doing?",
        "Random text with no calendar meaning"
    ]

class HeuristicParser:
    """Fast regex-based parser for common calendar patterns"""
    
    def __init__(self):
        self.patterns = RegexPatterns()
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Pre-compile all regex patterns for performance"""
        compiled = {}
        
        # Compile frequency patterns
        for freq, pattern_list in self.patterns.FREQUENCY_PATTERNS.items():
            compiled[f'freq_{freq}'] = [re.compile(p, re.IGNORECASE) for p in pattern_list]
        
        # Compile time patterns
        for time_type, pattern_list in self.patterns.TIME_PATTERNS.items():
            compiled[f'time_{time_type}'] = [re.compile(p, re.IGNORECASE) for p in pattern_list]
        
        # Compile recurring patterns
        for pattern_name, pattern in self.patterns.RECURRING_PATTERNS.items():
            compiled[f'recurring_{pattern_name}'] = re.compile(pattern, re.IGNORECASE)
        
        # Compile other patterns
        compiled['weekday'] = re.compile(self.patterns.WEEKDAY_PATTERN, re.IGNORECASE)
        compiled['ordinal'] = re.compile(self.patterns.ORDINAL_PATTERN, re.IGNORECASE)
        
        return compiled
    
    def parse(self, text: str) -> ParseResult:
        """
        Parse natural language text using regex patterns
        
        Args:
            text: Input text to parse
            
        Returns:
            ParseResult with extracted calendar information
        """
        text = text.strip().lower()
        result_data = {}
        confidence = 0.0
        raw_matches = {}
        
        try:
            # Extract title (everything before time/frequency indicators)
            title = self._extract_title(text)
            if title:
                result_data['title'] = title
                confidence += 0.2
            
            # Check for recurring patterns
            recurring_match = self._match_recurring_patterns(text)
            if recurring_match:
                result_data.update(recurring_match)
                confidence += 0.4
            
            # Extract time information
            time_match = self._extract_time(text)
            if time_match:
                result_data.update(time_match)
                confidence += 0.3
            
            # Extract duration
            duration_match = self._extract_duration(text)
            if duration_match:
                result_data.update(duration_match)
                confidence += 0.1
            
            # Determine event type
            if any(key in result_data for key in ['frequency', 'weekday', 'weekdays']):
                result_data['type'] = 'recurring'
            else:
                result_data['type'] = 'single'
            
            # Handle ambiguous cases
            if confidence < 0.5:
                suggestions = self._generate_suggestions(text, result_data)
                return ParseResult(
                    data=result_data,
                    confidence=confidence,
                    method='heuristic',
                    raw_matches=raw_matches,
                    suggestions=suggestions
                )
            
            return ParseResult(
                data=result_data,
                confidence=min(confidence, 0.95),  # Cap at 95%
                method='heuristic',
                raw_matches=raw_matches
            )
            
        except Exception as e:
            logger.error(f"Error in heuristic parsing: {e}")
            return ParseResult(
                data={'error': str(e)},
                confidence=0.0,
                method='heuristic'
            )
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract event title from text"""
        # Remove common calendar keywords to isolate title
        keywords = ['every', 'daily', 'weekly', 'monthly', 'at', 'from', 'to', 'for']
        
        # Split on time patterns first
        time_split = re.split(r'\bat\s+\d', text, 1)
        if len(time_split) > 1:
            potential_title = time_split[0].strip()
        else:
            # Split on frequency words
            freq_split = re.split(r'\b(every|daily|weekly|monthly)', text, 1)
            potential_title = freq_split[0].strip()
        
        if len(potential_title) > 2:  # Minimum reasonable title length
            return potential_title.title()
        
        return None
    
    def _match_recurring_patterns(self, text: str) -> Dict[str, Any]:
        """Match recurring event patterns"""
        result = {}
        
        # Check for frequency keywords
        for freq in ['daily', 'weekly', 'monthly', 'yearly']:
            if any(pattern.search(text) for pattern in self.compiled_patterns.get(f'freq_{freq}', [])):
                result['frequency'] = freq
                break
        
        # Check for specific weekdays
        weekday_match = self.compiled_patterns['weekday'].search(text)
        if weekday_match:
            weekday_text = weekday_match.group(1).lower()
            # Map variations to canonical weekday
            for canonical, variations in self.patterns.WEEKDAYS.items():
                if weekday_text in variations:
                    result['weekday'] = canonical
                    break
        
        # Check for ordinals (first, second, etc.)
        ordinal_match = self.compiled_patterns['ordinal'].search(text)
        if ordinal_match:
            ordinal_text = ordinal_match.group(1).lower()
            for canonical, variations in self.patterns.ORDINALS.items():
                if ordinal_text in variations:
                    result['ordinal'] = canonical
                    break
        
        # Check for interval patterns (every 2 weeks, etc.)
        interval_match = re.search(r'every\s+(\d+)', text)
        if interval_match:
            result['interval'] = int(interval_match.group(1))
        
        return result
    
    def _extract_time(self, text: str) -> Dict[str, Any]:
        """Extract time information"""
        result = {}
        
        # Try 12-hour format first
        for pattern in self.compiled_patterns.get('time_12_hour', []):
            match = pattern.search(text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                period = match.group(3).lower()
                
                # Convert to 24-hour format
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                
                result['start_time'] = f"{hour:02d}:{minute:02d}"
                break
        
        # Try 24-hour format if no 12-hour match
        if 'start_time' not in result:
            for pattern in self.compiled_patterns.get('time_24_hour', []):
                match = pattern.search(text)
                if match:
                    if ':' in match.group(0):
                        hour, minute = match.groups()
                    else:
                        # Handle HHMM format
                        time_str = match.group(1)
                        hour = time_str[:2] if len(time_str) == 4 else time_str[:-2]
                        minute = time_str[-2:]
                    
                    result['start_time'] = f"{int(hour):02d}:{int(minute):02d}"
                    break
        
        # Look for time ranges (from X to Y)
        range_pattern = re.compile(r'from\s+([^t]+)\s+to\s+(.+?)(?:\s|$)', re.IGNORECASE)
        range_match = range_pattern.search(text)
        if range_match:
            # Extract end time (simplified)
            end_time_text = range_match.group(2).strip()
            # This would need more sophisticated parsing
            # For now, just mark that there's an end time
            result['has_end_time'] = True
        
        return result
    
    def _extract_duration(self, text: str) -> Dict[str, Any]:
        """Extract duration information"""
        result = {}
        
        for pattern in self.patterns.DURATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                duration_value = match.group(1)
                duration_unit = match.group(2).lower()
                
                # Normalize units
                if duration_unit in ['hours', 'hrs', 'h']:
                    result['duration'] = f"{duration_value}h"
                elif duration_unit in ['minutes', 'mins', 'm']:
                    result['duration'] = f"{duration_value}m"
                break
        
        return result
    
    def _generate_suggestions(self, text: str, parsed_data: Dict[str, Any]) -> List[str]:
        """Generate suggestions for ambiguous inputs"""
        suggestions = []
        
        if 'weekday' in parsed_data and 'start_time' not in parsed_data:
            suggestions.append("Did you mean to specify a time?")
        
        if 'start_time' in parsed_data and parsed_data.get('start_time') == '02:00':
            suggestions.extend(["Did you mean 2 PM instead of 2 AM?"])
        
        if not parsed_data.get('title'):
            suggestions.append("Could you provide more details about the event?")
        
        return suggestions

class CalendarNLPParser:
    """
    Main NLP parser with cascading approach:
    1. Fast heuristic parsing for common patterns
    2. LLM fallback for complex cases
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.heuristic_parser = HeuristicParser()
        self.training_data = TrainingData()
        
        # Performance tracking
        self.parse_count = 0
        self.heuristic_success_count = 0
    
    def parse(self, text: str) -> ParseResult:
        """
        Main parsing entry point
        
        Args:
            text: Natural language input to parse
            
        Returns:
            ParseResult with extracted calendar information
        """
        self.parse_count += 1
        
        if not text or not text.strip():
            return ParseResult(
                data={'error': 'Empty input'},
                confidence=0.0,
                method='validation'
            )
        
        # Layer 1: Try heuristic parsing first
        heuristic_result = self.heuristic_parser.parse(text)
        
        confidence_threshold = self.config.get('heuristic_confidence_threshold', 0.6)
        
        if heuristic_result.confidence >= confidence_threshold:
            self.heuristic_success_count += 1
            logger.info(f"Parsed with heuristics (confidence: {heuristic_result.confidence:.2f}): {text}")
            return heuristic_result
        
        # Layer 2: LLM fallback (placeholder for now)
        # This would integrate with your LLM of choice
        logger.info(f"Heuristic parsing below threshold, would fallback to LLM: {text}")
        
        # For now, return heuristic result with lower confidence
        return heuristic_result
    
    def get_training_examples(self) -> List[Dict[str, Any]]:
        """Get training examples for model fine-tuning"""
        return self.training_data.TRAINING_EXAMPLES
    
    def get_negative_examples(self) -> List[str]:
        """Get negative examples (non-calendar text)"""
        return self.training_data.NEGATIVE_EXAMPLES
    
    def validate_parsing(self, text: str, expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parsing against expected output
        
        Args:
            text: Input text
            expected_output: Expected parsing result
            
        Returns:
            Validation results with accuracy metrics
        """
        result = self.parse(text)
        
        # Compare key fields
        matches = 0
        total_fields = 0
        
        for key in ['title', 'type', 'frequency', 'weekday', 'start_time']:
            if key in expected_output:
                total_fields += 1
                if result.data.get(key) == expected_output[key]:
                    matches += 1
        
        accuracy = matches / total_fields if total_fields > 0 else 0.0
        
        return {
            'input': text,
            'expected': expected_output,
            'actual': result.data,
            'accuracy': accuracy,
            'confidence': result.confidence,
            'method': result.method
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get parsing performance statistics"""
        heuristic_success_rate = (
            self.heuristic_success_count / self.parse_count 
            if self.parse_count > 0 else 0.0
        )
        
        return {
            'total_parses': self.parse_count,
            'heuristic_successes': self.heuristic_success_count,
            'heuristic_success_rate': heuristic_success_rate,
            'llm_fallback_rate': 1.0 - heuristic_success_rate
        }

# Convenience functions for external use
def parse_calendar_text(text: str, config: Dict[str, Any] = None) -> ParseResult:
    """Convenience function for quick parsing"""
    parser = CalendarNLPParser(config)
    return parser.parse(text)

def get_regex_patterns() -> RegexPatterns:
    """Get access to regex patterns for external use"""
    return RegexPatterns()

def get_training_data() -> TrainingData:
    """Get access to training data for model development"""
    return TrainingData()
