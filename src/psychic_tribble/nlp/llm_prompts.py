"""
LLM prompt templates and utilities for calendar event parsing
Supports multiple LLM providers and prompting strategies
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for LLM-based parsing"""
    provider: str  # 'openai', 'anthropic', 'ollama', 'local'
    model: str
    max_tokens: int = 500
    temperature: float = 0.1  # Low temperature for consistent parsing
    timeout: int = 30
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For local/custom endpoints

class PromptTemplates:
    """Collection of prompt templates for different parsing strategies"""
    
    # Base system prompt for calendar parsing
    SYSTEM_PROMPT = """You are an expert calendar event parser. Your task is to extract structured information from natural language text about calendar events and convert it into a standardized JSON format.

You must be precise and consistent. If information is ambiguous or missing, indicate uncertainty rather than guessing.

Output Format:
{
  "title": "string - event title/description",
  "type": "single|recurring - event type", 
  "start_date": "YYYY-MM-DD or null",
  "start_time": "HH:MM or null (24-hour format)",
  "end_time": "HH:MM or null (24-hour format)", 
  "duration": "XhYm or null (e.g., '1h30m')",
  "frequency": "daily|weekly|monthly|yearly or null",
  "interval": "number or null (e.g., 2 for 'every 2 weeks')",
  "weekdays": ["monday", "tuesday", ...] or null,
  "ordinal": "first|second|third|fourth|last or null", 
  "location": "string or null",
  "notes": "string or null",
  "confidence": "number 0-1",
  "ambiguities": ["list of ambiguous elements"] or null
}

Current date context: {current_date}
Current time context: {current_time}"""

    # Few-shot examples for training the LLM
    FEW_SHOT_EXAMPLES = [
        {
            "input": "Team meeting every Tuesday at 2pm",
            "output": {
                "title": "Team meeting",
                "type": "recurring",
                "start_date": None,
                "start_time": "14:00",
                "end_time": None,
                "duration": None,
                "frequency": "weekly", 
                "interval": 1,
                "weekdays": ["tuesday"],
                "ordinal": None,
                "location": None,
                "notes": None,
                "confidence": 0.95,
                "ambiguities": None
            }
        },
        {
            "input": "Dentist appointment tomorrow at 10:30 AM",
            "output": {
                "title": "Dentist appointment",
                "type": "single",
                "start_date": "{tomorrow_date}",
                "start_time": "10:30",
                "end_time": None,
                "duration": None,
                "frequency": None,
                "interval": None,
                "weekdays": None,
                "ordinal": None,
                "location": None,
                "notes": None,
                "confidence": 0.90,
                "ambiguities": None
            }
        },
        {
            "input": "Gym session every other Wednesday for 1 hour starting at 6pm",
            "output": {
                "title": "Gym session",
                "type": "recurring", 
                "start_date": None,
                "start_time": "18:00",
                "end_time": None,
                "duration": "1h",
                "frequency": "weekly",
                "interval": 2,
                "weekdays": ["wednesday"],
                "ordinal": None,
                "location": None,
                "notes": None,
                "confidence": 0.85,
                "ambiguities": None
            }
        },
        {
            "input": "Monthly team lunch first Friday of every month at noon",
            "output": {
                "title": "Monthly team lunch",
                "type": "recurring",
                "start_date": None,
                "start_time": "12:00", 
                "end_time": None,
                "duration": None,
                "frequency": "monthly",
                "interval": 1,
                "weekdays": ["friday"],
                "ordinal": "first",
                "location": None,
                "notes": None,
                "confidence": 0.90,
                "ambiguities": None
            }
        },
        {
            "input": "Meeting Tuesday",
            "output": {
                "title": "Meeting",
                "type": "single",
                "start_date": None,
                "start_time": None,
                "end_time": None,
                "duration": None,
                "frequency": None,
                "interval": None,
                "weekdays": ["tuesday"],
                "ordinal": None,
                "location": None,
                "notes": None,
                "confidence": 0.40,
                "ambiguities": ["unclear if this Tuesday or next Tuesday", "no time specified"]
            }
        }
    ]
    
    @classmethod
    def create_few_shot_prompt(cls, examples: List[Dict] = None) -> str:
        """Create a few-shot prompt with examples"""
        examples = examples or cls.FEW_SHOT_EXAMPLES
        
        prompt = "Here are some examples of how to parse calendar events:\n\n"
        
        for i, example in enumerate(examples, 1):
            prompt += f"Example {i}:\n"
            prompt += f"Input: \"{example['input']}\"\n"
            prompt += f"Output: {json.dumps(example['output'], indent=2)}\n\n"
        
        prompt += "Now parse this calendar event:\n"
        prompt += "Input: \"{input_text}\"\n"
        prompt += "Output:"
        
        return prompt
    
    @classmethod
    def create_chain_of_thought_prompt(cls) -> str:
        """Create a chain-of-thought prompt for complex parsing"""
        return """Parse this calendar request step by step:

Step 1: Identify the event type (single occurrence or recurring)
Step 2: Extract the event title/description
Step 3: Determine date and time information
Step 4: Identify any recurrence pattern
Step 5: Extract duration or end time if specified
Step 6: Note any location or additional details
Step 7: Assess confidence and identify ambiguities
Step 8: Format as JSON

Input: "{input_text}"

Step 1 - Event Type Analysis:
[Your analysis]

Step 2 - Title Extraction:
[Your analysis]

Step 3 - Date/Time Analysis: 
[Your analysis]

Step 4 - Recurrence Analysis:
[Your analysis]

Step 5 - Duration Analysis:
[Your analysis]

Step 6 - Additional Details:
[Your analysis]

Step 7 - Confidence Assessment:
[Your analysis]

Step 8 - Final JSON:
```json
[Your JSON output]
```"""

    @classmethod
    def create_structured_prompt(cls, input_text: str, context: Dict[str, Any] = None) -> str:
