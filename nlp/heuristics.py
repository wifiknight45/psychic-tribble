"""
Comprehensive heuristics and regex patterns for calendar event parsing
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, date
import calendar

class CalendarRegexPatterns:
    """
    Comprehensive collection of regex patterns for calendar parsing
    Organized by category for easy maintenance and testing
    """
    
    # Core weekday patterns with all common variations
    WEEKDAY_VARIATIONS = {
        'monday': ['monday', 'mon', 'mondays', 'm'],
        'tuesday': ['tuesday', 'tue', 'tues', 'tuesday\'s', 'tuesdays', 't'],
        'wednesday': ['wednesday', 'wed', 'wednesdays', 'w'],
        'thursday': ['thursday', 'thu', 'thur', 'thurs', 'thursdays', 'th'],
        'friday': ['friday', 'fri', 'fridays', 'f'],
        'saturday': ['saturday', 'sat', 'saturdays', 's'],
        'sunday': ['sunday', 'sun', 'sundays', 'su']
    }
    
    @classmethod
    def get_weekday_pattern(cls) -> str:
        """Generate comprehensive weekday pattern"""
        all_variations = []
        for variations in cls.WEEKDAY_VARIATIONS.values():
            all_variations.extend(variations)
        return r'\b(' + '|'.join(sorted(all_variations, key=len, reverse=True)) + r')\b'
    
    # Month patterns
    MONTH_VARIATIONS = {
        'january': ['january', 'jan'],
        'february': ['february', 'feb'],
        'march': ['march', 'mar'],
        'april': ['april', 'apr'],
        'may': ['may'],
        'june': ['june', 'jun'],
        'july': ['july', 'jul'],
        'august': ['august', 'aug'],
        'september': ['september', 'sept', 'sep'],
        'october': ['october', 'oct'],
        'november': ['november', 'nov'],
        'december': ['december', 'dec']
    }
    
    @classmethod
    def get_month_pattern(cls) -> str:
        """Generate comprehensive month pattern"""
        all_variations = []
        for variations in cls.MONTH_VARIATIONS.values():
            all_variations.extend(variations)
        return r'\b(' + '|'.join(sorted(all_variations, key=len, reverse=True)) + r')\b'
    
    # Ordinal number patterns
    ORDINAL_PATTERNS = {
        'written': r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty-first|twenty-second|twenty-third|twenty-fourth|twenty-fifth|twenty-sixth|twenty-seventh|twenty-eighth|twenty-ninth|thirtieth|thirty-first|last|final)\b',
        'numeric': r'\b(\d{1,2})(st|nd|rd|th)\b',
        'simple': r'\b(\d{1,2})\b'
    }
    
    # Frequency patterns with intervals
    FREQUENCY_PATTERNS = {
        'daily': [
            r'\b(daily|every\s+day|each\s+day)\b',
            r'\bevery\s+(\d+)\s+days?\b',
            r'\b(\d+)\s+times?\s+a\s+day\b',
            r'\bonce\s+a\s+day\b',
            r'\btwice\s+a\s+day\b'
        ],
        'weekly': [
            r'\b(weekly|every\s+week|each\s+week)\b',
            r'\bevery\s+(\d+)\s+weeks?\b',
            r'\bonce\s+a\s+week\b',
            r'\btwice\s+a\s+week\b',
            r'\b(\d+)\s+times?\s+a\s+week\b'
        ],
        'monthly': [
            r'\b(monthly|every\s+month|each\s+month)\b',
            r'\bevery\s+(\d+)\s+months?\b',
            r'\bonce\s+a\s+month\b',
            r'\btwice\s+a\s+month\b',
            r'\b(\d+)\s+times?\s+a\s+month\b'
        ],
        'yearly': [
            r'\b(yearly|annually|every\s+year|each\s+year)\b',
            r'\bevery\s+(\d+)\s+years?\b',
            r'\bonce\s+a\s+year\b',
            r'\bannually\b'
        ],
        'biweekly': [
            r'\b(biweekly|bi-weekly|every\s+other\s+week|every\s+2\s+weeks?)\b'
        ],
        'bimonthly': [
            r'\b(bimonthly|bi-monthly|every\s+other\s+month|every\s+2\s+months?)\b'
        ]
    }
    
    # Time patterns - comprehensive coverage
    TIME_PATTERNS = {
        '12_hour_with_minutes': [
            r'\b(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)\b',
            r'\b(\d{1,2})\.(\d{2})\s*(am|pm|a\.m\.|p\.m\.)\b'
        ],
        '12_hour_no_minutes': [
            r'\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)\b',
            r'\b(\d{1,2})\s*o\'?clock\s*(am|pm|a\.m\.|p\.m\.)?\b'
        ],
        '24_hour': [
            r'\b(\d{1,2}):(\d{2})\b(?!\s*(am|pm))',
            r'\b(\d{4})\b(?!\s*(am|pm))',  # 1430 format
        ],
        'relative_time': [
            r'\b(noon|midday)\b',
            r'\b(midnight)\b',
            r'\bin\s+the\s+(morning|afternoon|evening)\b',
            r'\b(early\s+morning|late\s+morning)\b',
            r'\b(early\s+afternoon|late\s+afternoon)\b',
            r'\b(early\s+evening|late\s+evening)\b'
        ],
        'time_ranges': [
            r'\b(\d{1,2}):?(\d{2})?\s*(am|pm)?\s*[-–—to]+\s*(\d{1,2}):?(\d{2})?\s*(am|pm)?\b',
            r'\bfrom\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?\s+to\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?\b',
            r'\bbetween\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?\s+and\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?\b'
        ]
    }
    
    # Duration patterns
    DURATION_PATTERNS = [
        r'\bfor\s+(\d+)\s+(hours?|hrs?|h)\b',
        r'\bfor\s+(\d+)\s+(minutes?|mins?|m)\b',
        r'\bfor\s+(\d+)\s+and\s+a\s+half\s+(hours?|hrs?)\b',
        r'\bfor\s+(\d+)\.5\s+(hours?|hrs?)\b',
        r'\bfor\s+(\d+)\s+(hours?|hrs?)\s+and\s+(\d+)\s+(minutes?|mins?)\b',
        r'\b(\d+)\s+(hours?|hrs?|h)\s+(long|duration)\b',
        r'\b(\d+)\s+(minutes?|mins?|m)\s+(long|duration)\b',
        r'\b(half\s+an?\s+hour|30\s+minutes?)\b',
        r'\b(an?\s+hour|1\s+hour)\b',
        r'\b(all\s+day|full\s+day)\b'
    ]
    
    # Date patterns
    DATE_PATTERNS = {
        'relative_days': [
            r'\b(today|tomorrow|yesterday)\b',
            r'\bthe\s+day\s+after\s+tomorrow\b',
            r'\bday\s+after\s+tomorrow\b'
        ],
        'relative_weeks': [
            r'\bnext\s+(week|' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r')\b',
            r'\blast\s+(week|' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r')\b',
            r'\bthis\s+(week|' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r')\b',
            r'\bcoming\s+(' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r')\b'
        ],
        'relative_future': [
            r'\bin\s+(\d+)\s+(days?|weeks?|months?|years?)\b',
            r'\b(\d+)\s+(days?|weeks?|months?|years?)\s+from\s+now\b'
        ],
        'absolute_dates': [
            r'\b' + get_month_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r'\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b',
            r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',
            r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b',
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
            r'\b(\d{1,2})\s+' + get_month_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r'\s+(\d{4})\b'
        ]
    }
    
    # Complex recurring patterns
    RECURRING_PATTERNS = {
        'every_weekday': r'\bevery\s+(' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r')\b',
        'every_nth_weekday': r'\bevery\s+(other|second|third|fourth)\s+(' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r')\b',
        'ordinal_weekday_of_month': ORDINAL_PATTERNS['written'] + r'\s+' + get_weekday_pattern.__func__(CalendarRegexPatterns),
        'weekdays_only': r'\b(weekdays?|business\s+days?|work\s+days?|working\s+days?)\b',
        'weekends_only': r'\b(weekends?|weekend\s+days?)\b',
        'multiple_weekdays': r'\b(' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r')\s+(and|&|,)\s+(' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r')\b',
        'except_pattern': r'\bexcept\s+(on\s+)?(' + get_weekday_pattern.__func__(CalendarRegexPatterns).strip(r'\b()') + r'|holidays?|vacation)\b'
    }

class CalendarHeuristics:
    """
    Advanced heuristics for calendar parsing beyond simple regex matching
    """
    
    @staticmethod
    def normalize_weekday(weekday_text: str) -> Optional[str]:
        """Convert any weekday variation to canonical form"""
        weekday_lower = weekday_text.lower().strip()
        
        for canonical, variations in CalendarRegexPatterns.WEEKDAY_VARIATIONS.items():
            if weekday_lower in variations:
                return canonical
        return None
    
    @staticmethod
    def normalize_month(month_text: str) -> Optional[str]:
        """Convert any month variation to canonical form"""
        month_lower = month_text.lower().strip()
        
        for canonical, variations in CalendarRegexPatterns.MONTH_VARIATIONS.items():
            if month_lower in variations:
                return canonical
        return None
    
    @staticmethod
    def parse_ordinal(ordinal_text: str) -> Optional[int]:
        """Convert ordinal text to number"""
        ordinal_lower = ordinal_text.lower().strip()
        
        ordinal_map = {
            'first': 1, '1st': 1,
            'second': 2, '2nd': 2,
            'third': 3, '3rd': 3,
            'fourth': 4, '4th': 4,
            'fifth': 5, '5th': 5,
            'last': -1, 'final': -1
        }
        
        return ordinal_map.get(ordinal_lower)
    
    @staticmethod
    def convert_12_to_24_hour(hour: int, minute: int, period: str) -> Tuple[int, int]:
        """Convert 12-hour time to 24-hour format"""
        period_lower = period.lower().replace('.', '')
        
        if period_lower in ['pm', 'p.m'] and hour != 12:
            hour += 12
        elif period_lower in ['am', 'a.m'] and hour == 12:
            hour = 0
        
        return hour, minute
    
    @staticmethod
    def infer_missing_time_info(time_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Infer missing time information from context"""
        result = {}
        
        # If just a number is given, infer AM/PM based on context
        if re.match(r'^\d{1,2}$', time_text.strip()):
            hour = int(time_text)
            
            # Business hours heuristic
            if 8 <= hour <= 17:
                result['likely_period'] = 'pm' if hour <= 6 else 'am'
                result['confidence_adjustment'] = -0.2  # Lower confidence due to ambiguity
            
            # Early hours likely AM
            elif 1 <= hour <= 7:
                result['likely_period'] = 'am'
            
            # Late hours likely PM
            elif hour >= 8:
                result['likely_period'] = 'pm'
        
        return result
    
    @staticmethod
    def resolve_relative_date(relative_text: str, reference_date: date = None) -> Optional[date]:
        """Resolve relative date expressions to absolute dates"""
        if reference_date is None:
            reference_date = date.today()
        
        relative_lower = relative_text.lower()
        
        if relative_lower == 'today':
            return reference_date
        elif relative_lower == 'tomorrow':
            return reference_date + timedelta(days=1)
        elif relative_lower == 'yesterday':
            return reference_date - timedelta(days=1)
        elif 'day after tomorrow' in relative_lower:
            return reference_date + timedelta(days=2)
        
        # Handle "next [weekday]"
        next_weekday_match = re.match(r'next\s+(\w+)', relative_lower)
        if next_weekday_match:
            weekday_name = CalendarHeuristics.normalize_weekday(next_weekday_match.group(1))
            if weekday_name:
                target_weekday = list(CalendarRegexPatterns.WEEKDAY_VARIATIONS.keys()).index(weekday_name)
                current_weekday = reference_date.weekday()
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:  # Target day is in the next week
                    days_ahead += 7
                return reference_date + timedelta(days=days_ahead)
        
        return None
    
    @staticmethod
    def extract_event_title(text: str, extracted_info: Dict[str, Any]) -> str:
        """Extract meaningful event title from text"""
        # Remove common calendar keywords and patterns
        text_copy = text.lower()
        
        # Keywords to remove
        removal_patterns = [
            r'\bevery\s+\w+',
            r'\bdaily\b|\bweekly\b|\bmonthly\b|\byearly\b',
            r'\bat\s+\d+',
            r'\bfrom\s+\d+',
            r'\bfor\s+\d+\s+\w+',
            r'\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'\b(today|tomorrow|yesterday|next|last|this)\b'
        ]
        
        for pattern in removal_patterns:
            text_copy = re.sub(pattern, ' ', text_copy, flags=re.IGNORECASE)
        
        # Clean up extra spaces and capitalize
        title = ' '.join(text_copy.split()).strip()
        if title:
            return title.title()
        
        # Fallback: use original text up to first time/frequency marker
        words = text.split()
        title_words = []
        
        for word in words:
            if re.match(r'\d+|every|daily|weekly|monthly|at|from|for', word.lower()):
                break
            title_words.append(word)
        
        return ' '.join(title_words).strip() or 'Event'
    
    @staticmethod
    def detect_ambiguity(text: str, parsed_data: Dict[str, Any]) -> List[str]:
        """Detect potential ambiguities in parsed data"""
        ambiguities = []
        
        # Time ambiguity (2 could be 2am or 2pm)
        if parsed_data.get('start_time') == '02:00':
            if not any(indicator in text.lower() for indicator in ['am', 'pm', 'morning', 'afternoon', 'night']):
                ambiguities.append('Time could be 2:00 AM or 2:00 PM')
        
        # Date ambiguity (Tuesday could be this Tuesday or next Tuesday)
        if 'weekday' in parsed_data and 'relative_date' not in parsed_data:
            if not any(indicator in text.lower() for indicator in ['this', 'next', 'coming', 'tomorrow']):
                ambiguities.append('Weekday could refer to this week or next week')
        
        # Missing duration or end time
        if parsed_data.get('start_time') and not parsed_data.get('end_time') and not parsed_data.get('duration'):
            ambiguities.append('Event duration not specified')
        
        # Vague frequency
        if 'frequency' not in parsed_data and any(word in text.lower() for word in ['regular', 'usual', 'normal']):
            ambiguities.append('Frequency not clearly specified')
        
        return ambiguities
    
    @staticmethod
    def calculate_confidence_score(matches: Dict[str, Any], text: str) -> float:
        """Calculate confidence score based on pattern matches"""
        confidence = 0.0
        
        # Base confidence for having any matches
        if matches:
            confidence = 0.3
        
        # Boost for specific patterns
        confidence_boosts = {
            'title': 0.15,
            'frequency': 0.25,
            'weekday': 0.20,
            'start_time': 0.25,
            'duration': 0.10,
            'end_time': 0.15
        }
        
        for key, boost in confidence_boosts.items():
            if key in matches and matches[key]:
                confidence += boost
        
        # Penalty for short or vague text
        if len(text.split()) < 3:
            confidence -= 0.2
        
        # Penalty for ambiguous patterns
        ambiguity_indicators = ['maybe', 'probably', 'might', 'could be', 'perhaps']
        if any(indicator in text.lower() for indicator in ambiguity_indicators):
            confidence -= 0.15
        
        # Boost for explicit time markers
        explicit_markers = ['at', 'from', 'to', 'every', 'daily', 'weekly']
        marker_count = sum(1 for marker in explicit_markers if marker in text.lower())
        confidence += min(marker_count * 0.05, 0.15)
        
        return max(0.0, min(1.0, confidence))

class PatternMatcher:
    """
    High-performance pattern matching utility with compiled regex patterns
    """
    
    def __init__(self):
        self.compiled_patterns = self._compile_all_patterns()
    
    def _compile_all_patterns(self) -> Dict[str, Any]:
        """Pre-compile all regex patterns for better performance"""
        compiled = {}
        patterns = CalendarRegexPatterns()
        
        # Compile frequency patterns
        for freq_type, pattern_list in patterns.FREQUENCY_PATTERNS.items():
            compiled[f'freq_{freq_type}'] = [
                re.compile(pattern, re.IGNORECASE) for pattern in pattern_list
            ]
        
        # Compile time patterns
        for time_type, pattern_list in patterns.TIME_PATTERNS.items():
            compiled[f'time_{time_type}'] = [
                re.compile(pattern, re.IGNORECASE) for pattern in pattern_list
            ]
        
        # Compile recurring patterns
        for pattern_name, pattern in patterns.RECURRING_PATTERNS.items():
            compiled[f'recurring_{pattern_name}'] = re.compile(pattern, re.IGNORECASE)
        
        # Compile other important patterns
        compiled['weekday'] = re.compile(patterns.get_weekday_pattern(), re.IGNORECASE)
        compiled['month'] = re.compile(patterns.get_month_pattern(), re.IGNORECASE)
        compiled['duration'] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns.DURATION_PATTERNS]
        
        return compiled
    
    def find_matches(self, text: str, pattern_type: str) -> List[re.Match]:
        """Find all matches for a specific pattern type"""
        patterns = self.compiled_patterns.get(pattern_type, [])
        if not isinstance(patterns, list):
            patterns = [patterns]
        
        matches = []
        for pattern in patterns:
            matches.extend(pattern.finditer(text))
        
        return matches
    
    def match_any(self, text: str, pattern_types: List[str]) -> Dict[str, List[re.Match]]:
        """Find matches for multiple pattern types"""
        results = {}
        for pattern_type in pattern_types:
            matches = self.find_matches(text, pattern_type)
            if matches:
                results[pattern_type] = matches
        
        return results
