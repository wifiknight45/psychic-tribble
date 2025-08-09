#!/usr/bin/env python3
"""
Calendar Parsing REPL Prototype

Quick prototyping environment for testing calendar parsing logic
with hard-coded input strings mapped to RRULE specifications.

Usage:
    python calendar_repl_prototype.py
    
Or import for interactive use:
    from calendar_repl_prototype import CalendarREPL
    repl = CalendarREPL()
    repl.run()
"""

import re
from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY, MO, TU, WE, TH, FR, SA, SU
from dateutil.parser import parse as date_parse
from typing import Dict, List, Any, Optional, Tuple
import json

class RRuleGenerator:
    """Convert parsed calendar data to RRULE specifications"""
    
    # Mapping weekday names to dateutil constants
    WEEKDAY_MAP = {
        'monday': MO, 'tuesday': TU, 'wednesday': WE, 'thursday': TH,
        'friday': FR, 'saturday': SA, 'sunday': SU
    }
    
    # Frequency mapping
    FREQ_MAP = {
        'daily': DAILY,
        'weekly': WEEKLY, 
        'monthly': MONTHLY,
        'yearly': YEARLY
    }
    
    @classmethod
    def create_rrule(cls, parsed_data: Dict[str, Any]) -> Optional[rrule]:
        """Create RRULE from parsed calendar data"""
        
        if parsed_data.get('type') != 'recurring':
            return None
        
        # Get frequency
        freq_str = parsed_data.get('frequency')
        if not freq_str or freq_str not in cls.FREQ_MAP:
            return None
        
        freq = cls.FREQ_MAP[freq_str]
        
        # Build RRULE parameters
        rrule_params = {'freq': freq}
        
        # Add interval if specified
        interval = parsed_data.get('interval', 1)
        if interval > 1:
            rrule_params['interval'] = interval
        
        # Add weekdays for weekly/monthly patterns
        weekdays = parsed_data.get('weekdays', [])
        if weekdays:
            weekday_objs = []
            for day in weekdays:
                if day in cls.WEEKDAY_MAP:
                    weekday_objs.append(cls.WEEKDAY_MAP[day])
            
            if weekday_objs:
                rrule_params['byweekday'] = weekday_objs
        
        # Handle ordinal patterns (e.g., "first Friday of month")
        ordinal = parsed_data.get('ordinal')
        if ordinal and freq == MONTHLY:
            ordinal_map = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'last': -1}
            if ordinal in ordinal_map and weekdays:
                # Convert to positioned weekday (e.g., first Friday = FR(1))
                pos = ordinal_map[ordinal]
                positioned_weekdays = []
                for day in weekdays:
                    if day in cls.WEEKDAY_MAP:
                        positioned_weekdays.append(cls.WEEKDAY_MAP[day](pos))
                rrule_params['byweekday'] = positioned_weekdays
        
        # Add start date (default to today if not specified)
        start_date = parsed_data.get('start_date')
        if start_date:
            try:
                dtstart = date_parse(start_date)
            except:
                dtstart = datetime.now()
        else:
            dtstart = datetime.now()
        
        rrule_params['dtstart'] = dtstart
        
        # Add count or until if specified
        count = parsed_data.get('count')
        if count:
            rrule_params['count'] = count
        
        until = parsed_data.get('until')
        if until:
            try:
                rrule_params['until'] = date_parse(until)
            except:
                pass
        
        try:
            return rrule(**rrule_params)
        except Exception as e:
            print(f"Error creating RRULE: {e}")
            return None

class CalendarPrototype:
    """Main prototype class with hard-coded test cases"""
    
    def __init__(self):
        self.test_cases = self._create_test_cases()
        self.rrule_generator = RRuleGenerator()
    
    def _create_test_cases(self) -> Dict[str, Dict[str, Any]]:
        """Hard-coded test cases with manual mapping to expected output"""
        
        return {
            # Simple recurring events
            "team meeting every tuesday at 2pm": {
                "title": "Team meeting",
                "type": "recurring",
                "frequency": "weekly",
                "weekdays": ["tuesday"],
                "start_time": "14:00",
                "interval": 1,
                "confidence": 0.95
            },
            
            "daily standup at 9:30 am": {
                "title": "Daily standup", 
                "type": "recurring",
                "frequency": "daily",
                "start_time": "09:30",
                "interval": 1,
                "confidence": 0.95
            },
            
            "gym every monday and wednesday at 6pm": {
                "title": "Gym",
                "type": "recurring", 
                "frequency": "weekly",
                "weekdays": ["monday", "wednesday"],
                "start_time": "18:00",
                "interval": 1,
                "confidence": 0.90
            },
            
            # Interval-based recurring
            "workout every other friday at 7am": {
                "title": "Workout",
                "type": "recurring",
                "frequency": "weekly", 
                "weekdays": ["friday"],
                "start_time": "07:00",
                "interval": 2,
                "confidence": 0.85
            },
            
            "monthly review meeting every 3 months": {
                "title": "Monthly review meeting",
                "type": "recurring",
                "frequency": "monthly",
                "interval": 3,
                "confidence": 0.80
            },
            
            # Ordinal patterns  
            "board meeting first monday of every month at 10am": {
                "title": "Board meeting",
                "type": "recurring",
                "frequency": "monthly",
                "weekdays": ["monday"], 
                "ordinal": "first",
                "start_time": "10:00",
                "interval": 1,
                "confidence": 0.90
            },
            
            "team lunch last friday of month at noon": {
                "title": "Team lunch",
                "type": "recurring",
                "frequency": "monthly",
                "weekdays": ["friday"],
                "ordinal": "last", 
                "start_time": "12:00",
                "interval": 1,
                "confidence": 0.85
            },
            
            # Single events
            "doctor appointment tomorrow at 3:30pm": {
                "title": "Doctor appointment",
                "type": "single",
                "relative_date": "tomorrow",
                "start_time": "15:30",
                "confidence": 0.90
            },
            
            "birthday party march 15th at 7pm": {
                "title": "Birthday party", 
                "type": "single",
                "absolute_date": "2024-03-15",
                "start_time": "19:00",
                "confidence": 0.90
            },
            
            # Duration-based events
            "project meeting for 2 hours starting at 9am": {
                "title": "Project meeting",
                "type": "single", 
                "start_time": "09:00",
                "duration": "2h",
                "confidence": 0.85
            },
            
            "weekly sync every thursday from 2pm to 3pm": {
                "title": "Weekly sync",
                "type": "recurring",
                "frequency": "weekly",
                "weekdays": ["thursday"],
                "start_time": "14:00", 
                "end_time": "15:00",
                "interval": 1,
                "confidence": 0.95
            },
            
            # Business day patterns
            "daily checkin weekdays at 8:30am": {
                "title": "Daily checkin",
                "type": "recurring",
                "frequency": "weekly",
                "weekdays": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "start_time": "08:30",
                "interval": 1,
                "confidence": 0.90
            },
            
            # Complex patterns
            "code review every tuesday and thursday at 10:30am for 1 hour": {
                "title": "Code review",
                "type": "recurring",
                "frequency": "weekly", 
                "weekdays": ["tuesday", "thursday"],
                "start_time": "10:30",
                "duration": "1h",
                "interval": 1,
                "confidence": 0.95
            },
            
            # Edge cases / ambiguous
            "meeting tuesday": {
                "title": "Meeting",
                "type": "single",
                "weekdays": ["tuesday"],
                "ambiguities": ["this tuesday or next tuesday?", "no time specified"],
                "confidence": 0.40
            },
            
            "call at 2": {
                "title": "Call", 
                "type": "single",
                "start_time": "14:00",  # Assume PM
                "ambiguities": ["2am or 2pm?"],
                "confidence": 0.50
            }
        }

class CalendarREPL:
    """Interactive REPL for testing calendar parsing"""
    
    def __init__(self):
        self.prototype = CalendarPrototype()
        self.history = []
        
    def run(self):
        """Start the interactive REPL"""
        print("🗓️  Calendar Parsing REPL Prototype")
        print("=" * 50)
        print("Commands:")
        print("  'list' - Show all test cases")
        print("  'test <input>' - Parse a specific input")
        print("  'all' - Run all test cases") 
        print("  'rrule <input>' - Show RRULE for input")
        print("  'history' - Show command history")
        print("  'help' - Show this help")
        print("  'quit' or 'exit' - Exit REPL")
        print("=" * 50)
        
        while True:
            try:
                command = input("\n📅 > ").strip()
                
                if not command:
                    continue
                    
                self.history.append(command)
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye! 👋")
                    break
                    
                elif command.lower() == 'help':
                    self._show_help()
                    
                elif command.lower() == 'list':
                    self._list_test_cases()
                    
                elif command.lower() == 'all':
                    self._run_all_tests()
                    
                elif command.lower() == 'history':
                    self._show_history()
                    
                elif command.lower().startswith('test '):
                    input_text = command[5:].strip()
                    self._test_input(input_text)
                    
                elif command.lower().startswith('rrule '):
                    input_text = command[6:].strip()
                    self._show_rrule(input_text)
                    
                else:
                    # Treat unknown commands as test input
                    self._test_input(command)
                    
            except KeyboardInterrupt:
                print("\n\nExiting... 👋")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show help information"""
        print("\n📚 Help:")
        print("  This REPL lets you test calendar parsing with predefined test cases.")
        print("  Type any natural language calendar input to see how it would be parsed.")
        print("  Use 'rrule <input>' to see the generated RRULE specification.")
        print("\n  Examples:")
        print("    > team meeting every tuesday at 2pm") 
        print("    > rrule daily standup at 9am")
        print("    > test gym every monday at 6pm")
    
    def _list_test_cases(self):
        """List all available test cases"""
        print(f"\n📋 Available Test Cases ({len(self.prototype.test_cases)}):")
        print("-" * 60)
        
        for i, input_text in enumerate(self.prototype.test_cases.keys(), 1):
            parsed = self.prototype.test_cases[input_text]
            event_type = parsed.get('type', 'unknown')
            confidence = parsed.get('confidence', 0)
            
            print(f"{i:2d}. \"{input_text}\"")
            print(f"     → {event_type} event (confidence: {confidence:.0%})")
    
    def _test_input(self, input_text: str):
        """Test parsing for a specific input"""
        input_lower = input_text.lower().strip()
        
        print(f"\n🔍 Testing: \"{input_text}\"")
        print("-" * 50)
        
        # Check if it's a predefined test case
        if input_lower in self.prototype.test_cases:
            parsed_data = self.prototype.test_cases[input_lower]
            print("✅ Found in test cases")
        else:
            print("⚠️  Not in predefined test cases - would need actual parsing")
            print("💡 Closest matches:")
            matches = self._find_similar_cases(input_lower)
            for match in matches[:3]:
                print(f"   - \"{match}\"")
            return
        
        # Display parsed data
        self._display_parsed_data(parsed_data)
        
        # Generate and display RRULE if applicable
        if parsed_data.get('type') == 'recurring':
            rrule_obj = self.prototype.rrule_generator.create_rrule(parsed_data)
            if rrule_obj:
                print(f"\n📝 RRULE: {rrule_obj}")
                
                # Show next few occurrences
                print("\n📅 Next 5 occurrences:")
                try:
                    next_events = list(rrule_obj[:5])
                    for i, event_date in enumerate(next_events, 1):
                        print(f"   {i}. {event_date.strftime('%Y-%m-%d %A')}")
                except Exception as e:
                    print(f"   Error generating occurrences: {e}")
    
    def _show_rrule(self, input_text: str):
        """Show RRULE for a specific input"""
        input_lower = input_text.lower().strip()
        
        if input_lower not in self.prototype.test_cases:
            print(f"❌ Input not found in test cases: \"{input_text}\"")
            return
        
        parsed_data = self.prototype.test_cases[input_lower]
        
        if parsed_data.get('type') != 'recurring':
            print(f"ℹ️  Input is not a recurring event: \"{input_text}\"")
            return
        
        rrule_obj = self.prototype.rrule_generator.create_rrule(parsed_data)
        
        if rrule_obj:
            print(f"\n📝 RRULE for: \"{input_text}\"")
            print(f"   {rrule_obj}")
            
            # Show human readable format
            print(f"\n🔤 Human readable: {rrule_obj.humanreadable()}")
            
            # Show raw RRULE string
            print(f"\n📋 RRULE string: {rrule_obj}")
            
            # Show parameters
            print(f"\n⚙️  Parameters:")
            for key, value in rrule_obj.__dict__.items():
                if not key.startswith('_') and value is not None:
                    print(f"   {key}: {value}")
        else:
            print(f"❌ Could not generate RRULE for: \"{input_text}\"")
    
    def _run_all_tests(self):
        """Run all test cases and show summary"""
        print(f"\n🧪 Running All Tests ({len(self.prototype.test_cases)} cases)")
        print("=" * 60)
        
        results = {"recurring": 0, "single": 0, "rrule_success": 0, "rrule_failed": 0}
        
        for input_text, parsed_data in self.prototype.test_cases.items():
            event_type = parsed_data.get('type', 'unknown')
            confidence = parsed_data.get('confidence', 0)
            
            print(f"📝 \"{input_text}\"")
            print(f"   Type: {event_type} | Confidence: {confidence:.0%}")
            
            results[event_type] = results.get(event_type, 0) + 1
            
            # Test RRULE generation for recurring events
            if event_type == 'recurring':
                rrule_obj = self.prototype.rrule_generator.create_rrule(parsed_data)
                if rrule_obj:
                    print(f"   ✅ RRULE: {rrule_obj}")
                    results["rrule_success"] += 1
                else:
                    print(f"   ❌ RRULE generation failed")
                    results["rrule_failed"] += 1
            
            print()
        
        # Show summary
        print("📊 Summary:")
        print(f"   Total cases: {len(self.prototype.test_cases)}")
        print(f"   Recurring events: {results.get('recurring', 0)}")
        print(f"   Single events: {results.get('single', 0)}")
        print(f"   RRULE success: {results['rrule_success']}")
        print(f"   RRULE failed: {results['rrule_failed']}")
        
        if results.get('recurring', 0) > 0:
            success_rate = results['rrule_success'] / results['recurring'] * 100
            print(f"   RRULE success rate: {success_rate:.1f}%")
    
    def _display_parsed_data(self, parsed_data: Dict[str, Any]):
        """Display parsed data in a readable format"""
        print("\n📋 Parsed Data:")
        
        # Core fields
        core_fields = ['title', 'type', 'frequency', 'weekdays', 'start_time', 'confidence']
        for field in core_fields:
            if field in parsed_data:
                value = parsed_data[field]
                if isinstance(value, list):
                    value = ', '.join(value)
                print(f"   {field}: {value}")
        
        # Optional fields
        optional_fields = ['interval', 'ordinal', 'duration', 'end_time', 'location', 'notes']
        for field in optional_fields:
            if field in parsed_data and parsed_data[field]:
                print(f"   {field}: {parsed_data[field]}")
        
        # Ambiguities
        if 'ambiguities' in parsed_data and parsed_data['ambiguities']:
            print("   ⚠️  Ambiguities:")
            for ambiguity in parsed_data['ambiguities']:
                print(f"      - {ambiguity}")
    
    def _find_similar_cases(self, input_text: str) -> List[str]:
        """Find similar test cases using basic text similarity"""
        import difflib
        
        test_case_keys = list(self.prototype.test_cases.keys())
        matches = difflib.get_close_matches(input_text, test_case_keys, n=5, cutoff=0.3)
        return matches
    
    def _show_history(self):
        """Show command history"""
        if not self.history:
            print("\n📝 No command history")
            return
        
        print(f"\n📝 Command History ({len(self.history)} commands):")
        for i, command in enumerate(self.history[-10:], 1):  # Show last 10
            print(f"   {i:2d}. {command}")

def main():
    """Main entry point for REPL"""
    repl = CalendarREPL()
    repl.run()

if __name__ == "__main__":
    # Quick demo if run directly
    print("🚀 Calendar Parsing Prototype Demo")
    
    prototype = CalendarPrototype()
    
    # Test a few cases
    test_inputs = [
        "team meeting every tuesday at 2pm",
        "daily standup at 9:30 am", 
        "board meeting first monday of every month at 10am"
    ]
    
    for input_text in test_inputs:
        print(f"\n🔍 Testing: \"{input_text}\"")
        if input_text in prototype.test_cases:
            parsed = prototype.test_cases[input_text]
            print(f"   ✅ Type: {parsed['type']}")
            print(f"   📝 Title: {parsed['title']}")
            
            if parsed['type'] == 'recurring':
                rrule_obj = prototype.rrule_generator.create_rrule(parsed)
                if rrule_obj:
                    print(f"   📅 RRULE: {rrule_obj}")
    
    print(f"\n🎯 Ready! Run with: python {__file__}")
    print("   Or start REPL: python -c 'from calendar_repl_prototype import CalendarREPL; CalendarREPL().run()'")
