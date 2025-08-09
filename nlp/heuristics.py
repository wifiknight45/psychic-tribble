#!/usr/bin/env python3

import re
from datetime import datetime
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from heuristics import (
    CalendarRegexPatterns,
    CalendarHeuristics,
    PatternMatcher
)

# maps for dateutil constants
WEEKDAY_CONST = {
    'monday': MO, 'tuesday': TU, 'wednesday': WE,
    'thursday': TH, 'friday': FR, 'saturday': SA, 'sunday': SU
}
FREQ_CONST = {
    'daily': DAILY, 'weekly': WEEKLY,
    'monthly': MONTHLY, 'yearly': YEARLY,
    'biweekly': WEEKLY, 'bimonthly': MONTHLY
}

def parse_recurrence(text: str, dtstart: datetime) -> dict:
    txt = text.lower()
    params = {'dtstart': dtstart}
    matcher = PatternMatcher()

    # 1. Frequency & Interval
    for freq, pats in CalendarRegexPatterns.FREQUENCY_PATTERNS.items():
        for pat in pats:
            m = re.search(pat, txt, re.IGNORECASE)
            if not m:
                continue
            interval = 2 if freq in ('biweekly','bimonthly') else \
                       int(m.group(1)) if m.groups() and m.group(1).isdigit() else 1
            params.update({
                'freq': FREQ_CONST[freq],
                'interval': interval
            })
            break
        if 'freq' in params:
            break

    # 2. “Nth weekday of month”
    ord_wd = CalendarRegexPatterns.RECURRING_PATTERNS['ordinal_weekday_of_month']
    m = re.search(ord_wd, txt, re.IGNORECASE)
    if m:
        nth = CalendarHeuristics.parse_ordinal(m.group(1))
        wd  = CalendarHeuristics.normalize_weekday(m.group(2))
        if nth and wd:
            return {
                'dtstart': dtstart,
                'freq': MONTHLY,
                'byweekday': WEEKDAY_CONST[wd],
                'bysetpos': nth
            }

    # 3. Weekly specific weekdays
    if params.get('freq') == WEEKLY:
        days = re.findall(CalendarRegexPatterns.get_weekday_pattern(), txt, re.IGNORECASE)
        if days:
            canon = [CalendarHeuristics.normalize_weekday(d) for d in days]
            params['byweekday'] = [WEEKDAY_CONST[d] for d in canon if d]
            return params

    # 4. Monthly on day N
    m = re.search(r'\bmonthly on day (\d{1,2})\b', txt)
    if m:
        return {
            'dtstart': dtstart,
            'freq': MONTHLY,
            'bymonthday': [int(m.group(1))]
        }

    if 'freq' in params:
        return params

    raise ValueError(f"Could not parse recurrence: “{text}”")

def prototype():
    start_dt = datetime.now()
    examples = [
        "daily at 9",
        "every 3 days",
        "first Tuesday of each month at 14",
        "every week on Mon, Wed and Fri",
        "biweekly",
        "today at 2",
        "monthly on day 15 until Dec 31 2025",
    ]

    for text in examples:
        print(f"\nInput: {text}")
        try:
            # Parse the recurrence rule
            rec_params = parse_recurrence(text, start_dt)
            rule = rrule(**rec_params)

            # 5. Resolve any “today”/“tomorrow” in dtstart
            if 'today' in text.lower() or 'tomorrow' in text.lower():
                rec_params['dtstart'] = CalendarHeuristics.resolve_relative_date(
                    text.split()[0], start_dt.date()
                )

            # 6. Infer missing AM/PM if time given without period
            time_nums = re.search(r'\b(\d{1,2})\b', text)
            if time_nums:
                missing = CalendarHeuristics.infer_missing_time_info(time_nums.group(1), {})
                if missing.get('likely_period'):
                    print("Inferred period:", missing['likely_period'])

            # 7. Extract title
            title = CalendarHeuristics.extract_event_title(text, rec_params)
            print("Title:", title)

            # 8. Construct RRULE string
            rfc = str(rule).split("RRULE:")[1]
            print("RRULE:", rfc)

            # 9. Next 5 occurrences
            for dt in list(rule)[:5]:
                print("  ", dt.strftime("%Y-%m-%d %H:%M"))

            # 10. Detect ambiguities and score
            ambig = CalendarHeuristics.detect_ambiguity(text, rec_params)
            score = CalendarHeuristics.calculate_confidence_score(rec_params, text)
            print("Ambiguities:", ambig or "None")
            print(f"Confidence: {score:.2f}")

        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    prototype()


# adjust this import path if needed
from heuristics import CalendarRegexPatterns, CalendarHeuristics

# map canonical weekday to dateutil constant
WEEKDAY_CONST = {
    'monday': MO, 'tuesday': TU, 'wednesday': WE,
    'thursday': TH, 'friday': FR, 'saturday': SA, 'sunday': SU
}

# frequency name → dateutil constant
FREQ_CONST = {
    'daily': DAILY,
    'weekly': WEEKLY,
    'monthly': MONTHLY,
    'yearly': YEARLY,
    'biweekly': WEEKLY,
    'bimonthly': MONTHLY
}

def parse_recurrence(text: str, dtstart: datetime):
    """
    Returns a dict of parameters for dateutil.rrule(...) based on heuristics.
    """
    txt = text.lower()
    params: dict = {'dtstart': dtstart}
    
    # 1. Frequency & Interval
    for freq_name, patterns in CalendarRegexPatterns.FREQUENCY_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, txt)
            if not m:
                continue

            base_freq = freq_name
            interval = 1

            # biweekly / bimonthly override
            if freq_name in ('biweekly','bimonthly'):
                interval = 2
            # capture “every N …” groups
            elif m.groups() and m.group(1) and m.group(1).isdigit():
                interval = int(m.group(1))

            params['freq']     = FREQ_CONST[base_freq]
            params['interval'] = interval
            break
        if 'freq' in params:
            break

    # 2. “Nth weekday of month” (e.g. “first Monday of each month”)
    ord_wd_pat = CalendarRegexPatterns.RECURRING_PATTERNS['ordinal_weekday_of_month']
    m = re.search(ord_wd_pat, txt)
    if m:
        # groups: (ordinal_word) (weekday_variation)
        ordinal_text = m.group(1)
        weekday_text = m.group(2)
        nth = CalendarHeuristics.parse_ordinal(ordinal_text)
        wd  = CalendarHeuristics.normalize_weekday(weekday_text)

        if nth and wd:
            params['freq']     = MONTHLY
            params['byweekday'] = WEEKDAY_CONST[wd]
            params['bysetpos']  = nth
            return params

    # 3. Weekly with specific weekdays (e.g. “every week on Mon, Wed, Fri”)
    wd_list = re.findall(CalendarRegexPatterns.get_weekday_pattern(), txt)
    if params.get('freq') == WEEKLY and wd_list:
        canon_days = [CalendarHeuristics.normalize_weekday(w) for w in wd_list]
        params['byweekday'] = [WEEKDAY_CONST[d] for d in canon_days if d]
        return params

    # 4. Monthly on day N (e.g. “monthly on day 15”)
    m = re.search(r'\bmonthly\s+on\s+day\s+(\d{1,2})\b', txt)
    if m:
        params['freq']       = MONTHLY
        params['bymonthday'] = [int(m.group(1))]
        return params

    # fallback: if freq only
    if 'freq' in params:
        return params

    raise ValueError(f"Could not parse recurrence: “{text}”")

def prototype():
    start = datetime.now()
    examples = [
        "daily",
        "every 3 days",
        "every week on Monday, Wednesday and Friday",
        "biweekly on tuesdays and thursdays",
        "first tuesday of each month",
        "monthly on day 15",
        "every year",
    ]

    for phrase in examples:
        print(f"\nInput: {phrase}")
        try:
            rule_params = parse_recurrence(phrase, start)
            rule = rrule(**rule_params)

            # Extract RRULE string, drop “DTSTART=”
            rfc = str(rule).split("RRULE:")[1]
            print("RRULE:", rfc)

            print("Next 5 occurrences:")
            for dt in list(rule)[:5]:
                print("  ", dt.strftime("%Y-%m-%d %H:%M"))
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    prototype()
