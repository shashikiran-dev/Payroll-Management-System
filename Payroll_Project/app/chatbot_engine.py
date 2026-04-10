import pickle
import os
import re
import requests as http_requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLASK_URL = "http://localhost:5000"

model      = pickle.load(open(os.path.join(BASE_DIR, "chatbot_model.pkl"), "rb"))
vectorizer = pickle.load(open(os.path.join(BASE_DIR, "vectorizer.pkl"),    "rb"))


# ─────────────────────────────────────────────
# STEP 1: Normalize — replace names with <PERSON>
# so ML model sees the same token it was trained on
# ─────────────────────────────────────────────
KEEP_WORDS = {
    'leave','balance','show','wfh','status','attendance','pending',
    'today','yesterday','tomorrow','all','employees','announcements',
    'give','me','the','of','is','what','work','from','home','days',
    'provide','details','requests','number','a','an','for'
}

def normalize_text(text):
    text = text.lower().strip()
    tokens = text.split()
    normalized = []
    for t in tokens:
        clean = re.sub(r'[^a-z]', '', t)
        if clean and clean not in KEEP_WORDS and len(clean) > 2:
            normalized.append('<PERSON>')
        else:
            normalized.append(t)
    return ' '.join(normalized)


# ─────────────────────────────────────────────
# STEP 2: Extract employee name from message
# ─────────────────────────────────────────────
def extract_employee_name(msg):
    stopwords = {
        'leave','balance','show','wfh','status','attendance','pending',
        'today','yesterday','tomorrow','all','employees','announcements',
        'give','me','the','of','is','what','work','from','home','days',
        'provide','details','requests','number','a','an','for',
        'my','their','his','her'
    }
    tokens = msg.lower().split()
    for token in reversed(tokens):
        clean = re.sub(r'[^a-z]', '', token)
        if clean and clean not in stopwords and len(clean) > 1:
            return clean.capitalize()
    return None


# ─────────────────────────────────────────────
# STEP 3: Extract number of days
# ─────────────────────────────────────────────
def extract_days(msg):
    match = re.search(r'(\d+)\s*day', msg.lower())
    return int(match.group(1)) if match else 7


# ─────────────────────────────────────────────
# STEP 4: Rule-based intent (runs before ML)
# ─────────────────────────────────────────────
def rule_based(msg):
    msg = msg.lower()

    is_all = 'all employee' in msg or 'all employees' in msg

    if is_all:
        if 'leave balance' in msg:                              return 'all_leave_balance'
        if 'attendance' in msg and 'today' in msg:             return 'all_today_attendance'
        if 'attendance' in msg and 'yesterday' in msg:         return 'all_yesterday_attendance'
        if 'attendance' in msg and 'tomorrow' in msg:          return 'all_tomorrow_attendance'
        if re.search(r'\d+\s*day', msg) and 'attendance' in msg: return 'all_attendance_number'
        if 'attendance' in msg:                                 return 'all_attendance'
        if 'leave' in msg and 'today' in msg:                  return 'all_today_leave'
        if 'leave' in msg and 'yesterday' in msg:              return 'all_yesterday_leave'
        if 'leave' in msg and 'tomorrow' in msg:               return 'all_tomorrow_leave'
        if 'leave' in msg:                                      return 'all_leave'
        if ('wfh' in msg or 'work from home' in msg) and 'today' in msg:     return 'all_today_wfh'
        if ('wfh' in msg or 'work from home' in msg) and 'yesterday' in msg: return 'all_yesterday_wfh'
        if ('wfh' in msg or 'work from home' in msg) and 'tomorrow' in msg:  return 'all_tomorrow_wfh'
        if 'wfh' in msg or 'work from home' in msg:            return 'all_wfh'
        if 'status' in msg and 'today' in msg:                 return 'all_today_status'
        if 'status' in msg and 'yesterday' in msg:             return 'all_yesterday_status'
        if 'status' in msg and 'tomorrow' in msg:              return 'all_tomorrow_status'
        if re.search(r'\d+\s*day', msg) and 'status' in msg:  return 'all_status_number'
        if 'status' in msg:                                     return 'all_status'
        if 'announc' in msg and 'today' in msg:                return 'all_today_announcement'
        if 'announc' in msg and 'yesterday' in msg:            return 'all_yesterday_announcement'
        if 'announc' in msg and 'tomorrow' in msg:             return 'all_tomorrow_announcement'
        if 'announc' in msg:                                    return 'all_announcement'

    # Specific employee queries
    if 'leave balance' in msg:                                  return 'leave_balance'
    if 'pending leave' in msg:                                  return 'pending_leave'
    if 'pending wfh' in msg or 'pending work from home' in msg: return 'pending_wfh'
    if 'announc' in msg and 'today' in msg:                    return 'today_announcement'
    if 'announc' in msg and 'yesterday' in msg:                return 'yesterday_announcement'
    if 'announc' in msg and 'tomorrow' in msg:                 return 'tomorrow_announcement'
    if 'announc' in msg:                                        return 'announcement'
    if 'attendance' in msg and 'today' in msg:                 return 'today_attendance'
    if 'attendance' in msg and 'yesterday' in msg:             return 'yesterday_attendance'
    if 'attendance' in msg and 'tomorrow' in msg:              return 'tomorrow_attendance'
    if 'attendance' in msg:                                     return 'attendance'
    if ('wfh' in msg or 'work from home' in msg) and 'today' in msg:     return 'today_wfh'
    if ('wfh' in msg or 'work from home' in msg) and 'yesterday' in msg: return 'yesterday_wfh'
    if ('wfh' in msg or 'work from home' in msg) and 'tomorrow' in msg:  return 'tomorrow_wfh'
    if 'wfh' in msg or 'work from home' in msg:                return 'wfh'
    if 'leave' in msg and 'today' in msg:                      return 'today_leave'
    if 'leave' in msg and 'yesterday' in msg:                  return 'yesterday_leave'
    if 'leave' in msg and 'tomorrow' in msg:                   return 'tomorrow_leave'
    if 'leave' in msg:                                          return 'leave'
    if re.search(r'\d+\s*day', msg) and 'status' in msg:      return 'status_number'
    if 'status' in msg and 'today' in msg:                     return 'today_status'
    if 'status' in msg and 'yesterday' in msg:                 return 'yesterday_status'
    if 'status' in msg and 'tomorrow' in msg:                  return 'tomorrow_status'
    if 'status' in msg:                                         return 'status'

    return None


# ─────────────────────────────────────────────
# STEP 5: Combined intent (rule first, ML fallback)
# ─────────────────────────────────────────────
def get_intent(msg):
    rule = rule_based(msg)
    if rule:
        return rule
    norm = normalize_text(msg)
    vec  = vectorizer.transform([norm])
    return model.predict(vec)[0]


# ─────────────────────────────────────────────
# STEP 6: Flask API helper
# ─────────────────────────────────────────────
def _post(endpoint, payload):
    try:
        r = http_requests.post(f"{FLASK_URL}{endpoint}", json=payload, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Flask call failed [{endpoint}]:", e)
    return None


# ─────────────────────────────────────────────
# STEP 7: Response builders (Admin-only)
# ─────────────────────────────────────────────

# --- LEAVE BALANCE ---
def get_leave_balance(name):
    data = _post('/chatbot/leave_by_name', {'name': name})
    if data and data.get('status') == 'success':
        d = data
        return (
            f"Leave balance for {d['employee_name']}:\n"
            f"  Sick: {d['sick_leave']}  |  Wedding: {d['wedding_leave']}  |  "
            f"Maternity: {d['maternity_leave']}  |  Paternity: {d['paternity_leave']}\n"
            f"  Total: {d['total_leaves']}  |  Taken: {d['taken_leaves']}  |  Remaining: {d['pending_leaves']}"
        )
    return f"No leave balance found for '{name}'."

def get_all_leave_balance():
    data = _post('/chatbot/all_leave_balance', {})
    if data and data.get('records'):
        lines = ["Leave balance — all employees:"]
        for r in data['records']:
            lines.append(f"  {r['Employee_Name']}: {r['Pending_leaves']} remaining")
        return '\n'.join(lines)
    return "No leave balance records found."

# --- ATTENDANCE ---
def get_attendance(name, day='current_month'):
    data = _post('/chatbot/attendance_by_name', {'name': name, 'day': day})
    if data and data.get('status') == 'success':
        return f"{name} — attendance ({day}): {data['days_present']} day(s) present."
    return f"Could not fetch attendance for '{name}'."

def get_all_attendance(day='current_month'):
    data = _post('/chatbot/all_attendance', {'day': day})
    if data and data.get('records'):
        lines = [f"Attendance ({day}) — all employees:"]
        for r in data['records']:
            lines.append(f"  {r['employee_name']}: {r['days']} day(s)")
        return '\n'.join(lines)
    return "No attendance records found."

def get_attendance_n_days(name, n):
    data = _post('/chatbot/attendance_by_name', {'name': name, 'day': f'last_{n}_days'})
    if data and data.get('status') == 'success':
        return f"{name} — last {n} days: {data['days_present']} day(s) present."
    return f"Could not fetch {n}-day attendance for '{name}'."

def get_all_attendance_n_days(n):
    data = _post('/chatbot/all_attendance', {'day': f'last_{n}_days'})
    if data and data.get('records'):
        lines = [f"Attendance (last {n} days) — all employees:"]
        for r in data['records']:
            lines.append(f"  {r['employee_name']}: {r['days']} day(s)")
        return '\n'.join(lines)
    return "No attendance records found."

# --- WFH ---
def get_wfh(name, day='all'):
    data = _post('/chatbot/wfh_by_name', {'name': name, 'day': day})
    if data and data.get('status') == 'success':
        count = data.get('count', 0)
        return f"{name} WFH requests ({day}): {count}."
    return f"Could not fetch WFH info for '{name}'."

def get_pending_wfh(name):
    data = _post('/chatbot/wfh_by_name', {'name': name, 'day': 'pending'})
    if data and data.get('status') == 'success':
        return f"{name} has {data.get('count', 0)} pending WFH request(s)."
    return f"Could not fetch pending WFH for '{name}'."

def get_all_wfh(day='all'):
    data = _post('/chatbot/all_wfh', {'day': day})
    if data and data.get('records'):
        lines = [f"WFH ({day}) — all employees:"]
        for r in data['records']:
            lines.append(f"  {r['Employee_Name']}: {r['Status']} ({r['Start_Date']} → {r['End_Date']})")
        return '\n'.join(lines)
    return f"No WFH records found ({day})."

# --- LEAVE STATUS ---
def get_leave(name, day='all'):
    data = _post('/chatbot/leave_by_name_day', {'name': name, 'day': day})
    if data and data.get('status') == 'success':
        recs = data.get('records', [])
        if not recs:
            return f"No leave records for {name} ({day})."
        lines = [f"Leave records for {name} ({day}):"]
        for r in recs:
            lines.append(f"  {r['Leave_Type']} | {r['Start_date']} → {r['End_date']} | {r['Status']}")
        return '\n'.join(lines)
    return f"Could not fetch leave info for '{name}'."

def get_pending_leave(name):
    data = _post('/chatbot/leave_by_name_day', {'name': name, 'day': 'pending'})
    if data and data.get('status') == 'success':
        recs = data.get('records', [])
        if not recs:
            return f"{name} has no pending leave requests."
        lines = [f"Pending leave requests for {name}:"]
        for r in recs:
            lines.append(f"  {r['Leave_Type']} | {r['Start_date']} → {r['End_date']}")
        return '\n'.join(lines)
    return f"Could not fetch pending leave for '{name}'."

# --- DAILY STATUS ---
def get_status(name, day='today'):
    data = _post('/chatbot/status_by_name', {'name': name, 'day': day})
    if data and data.get('status') == 'success':
        recs = data.get('records', [])
        if not recs:
            return f"No status updates found for {name} ({day})."
        lines = [f"Status updates for {name} ({day}):"]
        for r in recs:
            lines.append(f"  [{r['Date']}] {r['Status_Update']}")
        return '\n'.join(lines)
    return f"Could not fetch status for '{name}'."

def get_status_n_days(name, n):
    data = _post('/chatbot/status_by_name', {'name': name, 'day': f'last_{n}_days'})
    if data and data.get('status') == 'success':
        recs = data.get('records', [])
        if not recs:
            return f"No status updates found for {name} in last {n} days."
        lines = [f"Status updates for {name} (last {n} days):"]
        for r in recs:
            lines.append(f"  [{r['Date']}] {r['Status_Update']}")
        return '\n'.join(lines)
    return f"Could not fetch status for '{name}'."

def get_all_status(day='today'):
    data = _post('/chatbot/all_status', {'day': day})
    if data and data.get('records'):
        lines = [f"Status updates ({day}) — all employees:"]
        for r in data['records']:
            lines.append(f"  {r['Employee_Name']} [{r['Date']}]: {r['Status_Update']}")
        return '\n'.join(lines)
    return f"No status updates found ({day})."

def get_all_status_n_days(n):
    data = _post('/chatbot/all_status', {'day': f'last_{n}_days'})
    if data and data.get('records'):
        lines = [f"Status updates (last {n} days) — all employees:"]
        for r in data['records']:
            lines.append(f"  {r['Employee_Name']} [{r['Date']}]: {r['Status_Update']}")
        return '\n'.join(lines)
    return "No status records found."

# --- ANNOUNCEMENTS ---
def get_announcement(day='all'):
    data = _post('/chatbot/announcements', {'day': day})
    if data and data.get('records'):
        lines = [f"Announcements ({day}):"]
        for r in data['records']:
            lines.append(f"  [{r['Announcement_date']}] {r['Announcement']}")
        return '\n'.join(lines)
    return f"No announcements found ({day})."


# ─────────────────────────────────────────────
# MAIN — Admin chatbot entry point
# ─────────────────────────────────────────────
def process_query(msg, user_id=None):
    """
    Admin-only chatbot.
    Queries about ANY employee by name, or ALL employees.
    """
    intent = get_intent(msg)
    name   = extract_employee_name(msg)
    n      = extract_days(msg)

    # ── ALL EMPLOYEES ──────────────────────────────────────────
    if intent == 'all_leave_balance':           return get_all_leave_balance()
    if intent == 'all_attendance':              return get_all_attendance('current_month')
    if intent == 'all_today_attendance':        return get_all_attendance('today')
    if intent == 'all_yesterday_attendance':    return get_all_attendance('yesterday')
    if intent == 'all_tomorrow_attendance':     return get_all_attendance('tomorrow')
    if intent == 'all_attendance_number':       return get_all_attendance_n_days(n)
    if intent == 'all_leave':                   return get_all_wfh('all')
    if intent == 'all_today_leave':             return get_all_wfh('today')
    if intent == 'all_yesterday_leave':         return get_all_wfh('yesterday')
    if intent == 'all_tomorrow_leave':          return get_all_wfh('tomorrow')
    if intent == 'all_wfh':                     return get_all_wfh('all')
    if intent == 'all_today_wfh':               return get_all_wfh('today')
    if intent == 'all_yesterday_wfh':           return get_all_wfh('yesterday')
    if intent == 'all_tomorrow_wfh':            return get_all_wfh('tomorrow')
    if intent == 'all_status':                  return get_all_status('all')
    if intent == 'all_today_status':            return get_all_status('today')
    if intent == 'all_yesterday_status':        return get_all_status('yesterday')
    if intent == 'all_tomorrow_status':         return get_all_status('tomorrow')
    if intent == 'all_status_number':           return get_all_status_n_days(n)
    if intent == 'all_announcement':            return get_announcement('all')
    if intent == 'all_today_announcement':      return get_announcement('today')
    if intent == 'all_yesterday_announcement':  return get_announcement('yesterday')
    if intent == 'all_tomorrow_announcement':   return get_announcement('tomorrow')

    # ── SPECIFIC EMPLOYEE ──────────────────────────────────────
    if not name:
        return "Please mention the employee name.\nExample: 'Show leave balance of Ravi'"

    if intent == 'leave_balance':           return get_leave_balance(name)
    if intent == 'pending_leave':           return get_pending_leave(name)
    if intent == 'pending_wfh':             return get_pending_wfh(name)
    if intent == 'attendance':              return get_attendance(name, 'current_month')
    if intent == 'today_attendance':        return get_attendance(name, 'today')
    if intent == 'yesterday_attendance':    return get_attendance(name, 'yesterday')
    if intent == 'tomorrow_attendance':     return get_attendance(name, 'tomorrow')
    if intent == 'wfh':                     return get_wfh(name, 'all')
    if intent == 'today_wfh':              return get_wfh(name, 'today')
    if intent == 'yesterday_wfh':          return get_wfh(name, 'yesterday')
    if intent == 'tomorrow_wfh':           return get_wfh(name, 'tomorrow')
    if intent == 'leave':                   return get_leave(name, 'all')
    if intent == 'today_leave':             return get_leave(name, 'today')
    if intent == 'yesterday_leave':         return get_leave(name, 'yesterday')
    if intent == 'tomorrow_leave':          return get_leave(name, 'tomorrow')
    if intent == 'status':                  return get_status(name, 'all')
    if intent == 'today_status':            return get_status(name, 'today')
    if intent == 'yesterday_status':        return get_status(name, 'yesterday')
    if intent == 'tomorrow_status':         return get_status(name, 'tomorrow')
    if intent == 'status_number':           return get_status_n_days(name, n)
    if intent == 'announcement':            return get_announcement('all')
    if intent == 'today_announcement':      return get_announcement('today')
    if intent == 'yesterday_announcement':  return get_announcement('yesterday')
    if intent == 'tomorrow_announcement':   return get_announcement('tomorrow')

    return (
        "Sorry, I didn't understand that. Try:\n"
        "  • Show leave balance of [name]\n"
        "  • Show today attendance of all employees\n"
        "  • Show pending WFH requests of [name]\n"
        "  • Give me 7 days status of [name]\n"
        "  • Show today announcements"
    )