from django.shortcuts import render, redirect
from app.views import login_required, get_session_user
import requests
from datetime import datetime, timedelta
import pymysql
from django.http import HttpResponse

BASE = "http://localhost:5000"

# ─────────────────────────────────────────────────────
# ENDPOINT REFERENCE (from app.py):
#
# /get_employees_count          POST {}
#   → all_employee_name_id[{Employee_id, Employee_Name, Team_lead, Manager_name}]
#
# /get_all_leaves_summary       POST {}
#   → all_leaves[{Employee_id, Employee_Name, Applied_on, Start_date, End_date,
#                 No_of_Days, Leave_Type, Reason, Request_id, Status,
#                 Approved_By_Whom(history only)}]
#
# /get_all_attendance_summary   POST {}
#   → all_rows[{employee_id, employee_name, Date}]   ← summary only (no clock times)
#
# /get_employee_attendance      POST {employee_id}
#   → employee_clock_info[{Date, clock_in_time, clock_out_time, Avg_working_hrs,
#                           employee_name, Employee_id}]
#
# /admin_get_attendance         POST {Request_Type: Last_Month|Last_week|Last_Day, Emp_id}
#   → Clock_Info[{Date, employee_name, clock_in_time, clock_out_time,
#                 clock_in_location, Avg_working_hrs}]
#
# /admin_get_status             POST {Request_Type: Last_Month|Last_week|Last_Day, Emp_id}
#   → Status_Info[{Date, Employee_id, Employee_Name, Status_Update, Issues,
#                  Completed_Task, Feature_Targets}]
#
# /get_employee_WFH_Info        POST {employee_id}
#   → employee_Emp_WHF_Info[{Request_id, Employee_Id, Employee_Name, Applied_on,
#                             Start_Date, End_Date, No_of_Days, Reason, Status}]
#
# /update_work_from_home        POST {request_id, Action_Status: "accept"|"reject"}
#
# /WFH_accept/<request_id>/<person_name>   GET/POST
# /WFH_Reject/<request_id>/<person_name>  GET/POST
#
# /get_employee_status_Info     POST {employee_id}
#   → employee_Emp_Status_Info[{Date, Employee_id, Employee_Name, Status_Update,
#                                Issues, Completed_Task, Feature_Targets}]
#
# /Get_ClockAdj                 POST {Selected_Date, user_id}
#   → Clock_Info[{Date, clock_in_time, clock_out_time, Avg_working_hrs}]
#   NOTE: No endpoint to list ALL clock adj requests for a team.
#         ClockAdjustment table fields: Employee_id, Employee_Name, Request_Type,
#         Clock_In, Clock_Out, Reason, Selected_Date, Inserting_Date, Request_Status
#         We query it directly through /admin_get_status style or use attendance_data.
#
# /accept_req/<Employee_Id>/<Request_Type>/<Selected_Date>/<person_name>/<Employee_Name>
# /reject_req/<Employee_Id>/<Selected_Date>/<Request_Type>/<person_name>
#
# /accept/<request_id>/<person_name>   POST  (leave)
# /reject/<request_id>/<person_name>   POST  (leave)
#
# /Queries_Info                 POST {employee_id, request: "all"}
#   → Queries_Info[{query_id, Employee_id, Employee_Name, Employee_Email,
#                   Date, Time, Query, Status, Reply}]
#
# /query                        POST {Employee_id, Employee_Name, Employee_Email, Query}
# /reply_query                  POST {query_id, answer}
# /employee_queries             POST {employee_id}
#   → Queries_Info[{query_id, Date, Time, Query, Status, Reply}]
#
# /Announcement_Info            POST {}
#   → Announcement_Info[{Employee_Name, Announcement, Announcement_date}]
#
# /profile                      POST {employee_id}
#   → Profile_Info{Employee_Name, Username, Employee_id, Employee_email,
#                  Phone_Number, Department, Position, Gender, Address,
#                  Skills, Team_lead, Team_lead_email, Manager_name,
#                  Manager_email, Work_location}
#
# /clock_in                     POST {employee_id, employee_name, historic,
#                                     district, button_name: "clock_in"|"clock_out"}
#
# /get_clock_in                 POST {employee_id}
#   → current_time, current_date, Profile_Info
#
# /attendance_data              POST {start_date, end_date}
#   → Attendance_Info[{Date, clock_in_time, clock_out_time, Avg_working_hrs, ...}]
#
# /status_data                  POST {start_date, end_date}
#   → daily_status_data[...]
#
# ─────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────
def get_team_members(team_lead_name):
    """
    Returns (all_employees, team_members, team_ids).
    Uses /get_employees_count → all_employee_name_id[Employee_id, Employee_Name, Team_lead]
    Matches by Team_lead name (case-insensitive).
    """
    all_employees = []
    try:
        res = requests.post(f"{BASE}/get_employees_count", json={})
        if res.status_code == 200:
            all_employees = res.json().get('all_employee_name_id', [])
    except Exception as e:
        print("get_team_members error:", e)

    team_members = [
        emp for emp in all_employees
        if str(emp.get('Team_lead', '')).strip().lower() ==
           str(team_lead_name).strip().lower()
    ]
    team_ids = [str(emp.get('Employee_id')) for emp in team_members]
    return all_employees, team_members, team_ids


def _tl_only(request, session_user):
    """Return True if NOT teamlead (caller should redirect)."""
    return session_user['user_type'].lower() != "teamlead"


# ─────────────────────────────────────────────────────
# DASHBOARD
# Uses /get_all_attendance_summary → all_rows[{employee_id, Date}]
# Uses /get_all_leaves_summary     → all_leaves[{Employee_id, Status}]
# Uses /get_employees_count        → Work_From_Home_Info[{Employee_id, Status}]
# ─────────────────────────────────────────────────────
@login_required
def teamlead_dashboard(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    team_lead_name = session_user['username']
    _, team_members, team_ids = get_team_members(team_lead_name)
    team_size = len(team_members)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Today's attendance — /get_all_attendance_summary → all_rows[employee_id, Date]
    today_attendance = 0
    try:
        res = requests.post(f"{BASE}/get_all_attendance_summary", json={})
        if res.status_code == 200:
            for row in res.json().get('all_rows', []):
                if (str(row.get('Date', ''))[:10] == today_str and
                        str(row.get('employee_id')) in team_ids):
                    today_attendance += 1
    except Exception as e:
        print("Dashboard attendance error:", e)

    # Pending leaves — /get_all_leaves_summary → all_leaves[Employee_id, Status]
    pending_leaves = 0
    try:
        res = requests.post(f"{BASE}/get_all_leaves_summary", json={})
        if res.status_code == 200:
            for lv in res.json().get('all_leaves', []):
                if (lv.get('Status') == 'Waiting' and
                        str(lv.get('Employee_id')) in team_ids):
                    pending_leaves += 1
    except Exception as e:
        print("Dashboard leave error:", e)

    # Pending WFH — /get_employees_count → Work_From_Home_Info[Employee_id, Status]
    pending_wfh = 0
    pending_clk = 0
    try:
        res = requests.post(f"{BASE}/get_employees_count", json={})
        if res.status_code == 200:
            for w in res.json().get('Work_From_Home_Info', []):
                if (w.get('Status') == 'Waiting' and
                        str(w.get('Employee_id')) in team_ids):
                    pending_wfh += 1
    except Exception as e:
        print("Dashboard WFH error:", e)

    # Pending clock adjustments — /attendance_data with wide date range as fallback
    # (no dedicated "list all ClockAdj" endpoint — we use attendance_data across last month
    # and cross-reference; for the KPI we just show 0 if not available)
    # A proper approach: query via date range attendance_data or skip if not available.

    return render(request, 'teamlead/team_dashboard.html', {
        **session_user,
        "team_size": team_size,
        "today_attendance": today_attendance,
        "pending_leaves": pending_leaves,
        "pending_wfh": pending_wfh,
        "pending_clk": pending_clk,
        "team_members": team_members,
    })


# ─────────────────────────────────────────────────────
# MY TEAM MEMBERS
# /get_all_attendance_summary → all_rows[employee_id, Date]
# /get_all_leaves_summary     → all_leaves[Employee_id, Status]
# /profile                    → Profile_Info.Employee_email, Phone_Number
#   NOTE: get_employees_count only returns Employee_id, Employee_Name, Team_lead.
#         Email/phone come from /profile per employee.
#         To avoid N+1 calls, we use /get_all_attendance_summary for today badge
#         and accept that email/phone need individual /profile calls.
#         Compromise: call /profile only if team is small, else show N/A.
# ─────────────────────────────────────────────────────
@login_required
def my_team_members(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    team_lead_name = session_user['username']
    _, team_members, team_ids = get_team_members(team_lead_name)

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Build today's attendance set
    present_ids = set()
    try:
        res = requests.post(f"{BASE}/get_all_attendance_summary", json={})
        if res.status_code == 200:
            for row in res.json().get('all_rows', []):
                if str(row.get('Date', ''))[:10] == today_str:
                    present_ids.add(str(row.get('employee_id')))
    except Exception as e:
        print("my_team attendance error:", e)

    # Build leave status map from /get_all_leaves_summary
    leave_map = {}
    try:
        res = requests.post(f"{BASE}/get_all_leaves_summary", json={})
        if res.status_code == 200:
            for lv in res.json().get('all_leaves', []):
                eid = str(lv.get('Employee_id'))
                if lv.get('Status') == 'Waiting':
                    leave_map[eid] = 'Pending'
                elif lv.get('Status') == 'Accepted' and eid not in leave_map:
                    leave_map[eid] = 'Approved'
    except Exception as e:
        print("my_team leave error:", e)

    # Fetch profile info per team member (email, phone, dept, position)
    # Uses /profile POST {employee_id} → Profile_Info
    profile_map = {}
    for emp in team_members:
        eid = str(emp.get('Employee_id'))
        try:
            res = requests.post(f"{BASE}/profile", json={"employee_id": eid})
            if res.status_code == 200:
                p = res.json().get('Profile_Info') or {}
                profile_map[eid] = p
        except Exception as e:
            print(f"Profile fetch error for {eid}:", e)

    final_team = []
    for emp in team_members:
        eid = str(emp.get('Employee_id'))
        p = profile_map.get(eid, {})
        final_team.append({
            "name":        emp.get('Employee_Name'),
            "id":          eid,
            "email":       p.get('Employee_email', 'N/A'),
            "phone":       p.get('Phone_Number', 'N/A'),
            "department":  p.get('Department', 'N/A'),
            "position":    p.get('Position', 'N/A'),
            "attendance":  "Present" if eid in present_ids else "Absent",
            "leave_status": leave_map.get(eid, 'None'),
        })

    return render(request, 'teamlead/my_team.html', {
        **session_user, "team_members": final_team
    })


# ─────────────────────────────────────────────────────
# TEAM MEMBER PROFILE
# /profile POST {employee_id} → Profile_Info
# /get_leaverequest_data POST {employee_id} → Employee_Leave_request_data
# ─────────────────────────────────────────────────────
@login_required
def team_member_profile(request, emp_id):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    profile = {}
    leaves = []

    try:
        res = requests.post(f"{BASE}/profile", json={"employee_id": emp_id})
        if res.status_code == 200:
            profile = res.json().get('Profile_Info') or {}
    except Exception as e:
        print("Profile error:", e)

    try:
        res = requests.post(f"{BASE}/get_leaverequest_data", json={"employee_id": emp_id})
        if res.status_code == 200:
            leaves = res.json().get('Employee_Leave_request_data', [])
    except Exception as e:
        print("Leave request data error:", e)

    return render(request, 'teamlead/team_member_profile.html', {
        **session_user,
        "employee": profile,
        "leaves": leaves,
        "emp_id": emp_id,
    })


# ─────────────────────────────────────────────────────
# LEAVE REQUESTS
# /get_all_leaves_summary POST {} → all_leaves[Employee_id, Status, ...]
# /accept/<request_id>/<person_name>  POST
# /reject/<request_id>/<person_name>  POST
# ─────────────────────────────────────────────────────
@login_required
def team_leave_requests(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, _, team_ids = get_team_members(session_user['username'])
    status_filter = request.GET.get('status', 'All')

    leaves = []
    try:
        res = requests.post(f"{BASE}/get_all_leaves_summary", json={})
        if res.status_code == 200:
            leaves = [
                lv for lv in res.json().get('all_leaves', [])
                if str(lv.get('Employee_id')) in team_ids
            ]
    except Exception as e:
        print("team_leave_requests error:", e)

    if status_filter != 'All':
        leaves = [lv for lv in leaves if lv.get('Status') == status_filter]

    return render(request, 'teamlead/team_leave.html', {
        **session_user, "leaves": leaves, "current_filter": status_filter
    })


@login_required
def team_leave_accept(request, leave_id, name):
    try:
        requests.post(f"{BASE}/accept/{leave_id}/{name}")
    except Exception as e:
        print("Leave accept error:", e)
    return redirect('teamleave_requests')


@login_required
def team_leave_reject(request, leave_id, name):
    try:
        requests.post(f"{BASE}/reject/{leave_id}/{name}")
    except Exception as e:
        print("Leave reject error:", e)
    return redirect('teamleave_requests')


@login_required
def team_leave_history(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, _, team_ids = get_team_members(session_user['username'])
    search    = request.GET.get('search', '').strip().lower()
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')

    leaves = []
    try:
        res = requests.post(f"{BASE}/get_all_leaves_summary", json={})
        if res.status_code == 200:
            leaves = [
                lv for lv in res.json().get('all_leaves', [])
                if str(lv.get('Employee_id')) in team_ids
            ]
    except Exception as e:
        print("team_leave_history error:", e)

    if search:
        leaves = [lv for lv in leaves
                  if search in str(lv.get('Employee_Name', '')).lower()]
    if date_from:
        leaves = [lv for lv in leaves
                  if str(lv.get('Start_date', ''))[:10] >= date_from]
    if date_to:
        leaves = [lv for lv in leaves
                  if str(lv.get('Start_date', ''))[:10] <= date_to]

    return render(request, 'teamlead/team_leave_history.html', {
        **session_user, "leaves": leaves,
        "search": search, "date_from": date_from, "date_to": date_to
    })


# ─────────────────────────────────────────────────────
# WFH REQUESTS
# /get_employees_count POST {} → Work_From_Home_Info[Request_id, Employee_id,
#                                  Employee_Name, Applied_on, Start_Date,
#                                  End_Date, No_of_Days, Reason, Status]
# /update_work_from_home POST {request_id, Action_Status: "accept"|"reject"}
# ─────────────────────────────────────────────────────
@login_required
def team_wfh_requests(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, _, team_ids = get_team_members(session_user['username'])
    status_filter = request.GET.get('status', 'All')
    search        = request.GET.get('search', '').strip().lower()

    all_wfh = []
    try:
        res = requests.post(f"{BASE}/get_employees_count", json={})
        if res.status_code == 200:
            all_wfh = [
                w for w in res.json().get('Work_From_Home_Info', [])
                if str(w.get('Employee_id')) in team_ids
            ]
    except Exception as e:
        print("team_wfh_requests error:", e)

    if status_filter != 'All':
        all_wfh = [w for w in all_wfh if w.get('Status') == status_filter]
    if search:
        all_wfh = [w for w in all_wfh
                   if search in str(w.get('Employee_Name', '')).lower()]

    counts = {
        "pending":  sum(1 for w in all_wfh if w.get('Status') == 'Waiting'),
        "accepted": sum(1 for w in all_wfh if w.get('Status') == 'Accepted'),
        "rejected": sum(1 for w in all_wfh if w.get('Status') == 'Rejected'),
    }

    return render(request, 'teamlead/team_wfh.html', {
        **session_user, "wfh_list": all_wfh,
        "current_filter": status_filter, "search": search, "counts": counts
    })


@login_required
def team_wfh_update(request, req_id, action):
    """
    /update_work_from_home POST {request_id, Action_Status: "accept"|"reject"}
    """
    try:
        requests.post(
            f"{BASE}/update_work_from_home",
            json={"request_id": req_id, "Action_Status": action}
        )
    except Exception as e:
        print("team_wfh_update error:", e)
    return redirect('team_wfh_requests')


@login_required
def team_wfh_history(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, _, team_ids = get_team_members(session_user['username'])
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    period    = request.GET.get('period', '')
    today     = datetime.now().date()

    if period == 'week':
        date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to   = today.strftime("%Y-%m-%d")
    elif period == 'month':
        date_from = today.replace(day=1).strftime("%Y-%m-%d")
        date_to   = today.strftime("%Y-%m-%d")

    all_wfh = []
    try:
        res = requests.post(f"{BASE}/get_employees_count", json={})
        if res.status_code == 200:
            all_wfh = [
                w for w in res.json().get('Work_From_Home_Info', [])
                if str(w.get('Employee_id')) in team_ids
            ]
    except Exception as e:
        print("team_wfh_history error:", e)

    if date_from:
        all_wfh = [w for w in all_wfh
                   if str(w.get('Start_Date', ''))[:10] >= date_from]
    if date_to:
        all_wfh = [w for w in all_wfh
                   if str(w.get('Start_Date', ''))[:10] <= date_to]

    # Per-employee WFH day count
    wfh_counts = {}
    for w in all_wfh:
        n = w.get('Employee_Name', 'Unknown')
        wfh_counts[n] = wfh_counts.get(n, 0) + 1

    return render(request, 'teamlead/team_wfh_history.html', {
        **session_user, "wfh_list": all_wfh, "wfh_counts": wfh_counts,
        "date_from": date_from, "date_to": date_to, "period": period
    })


# ─────────────────────────────────────────────────────
# ATTENDANCE OVERVIEW
# /attendance_data POST {start_date, end_date}
#   → Attendance_Info[{Date, employee_id, employee_name, clock_in_time,
#                       clock_out_time, Avg_working_hrs, ...}]
# For today: start_date=today, end_date=today
# ─────────────────────────────────────────────────────
@login_required
def team_attendance_overview(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, team_members, team_ids = get_team_members(session_user['username'])
    today_str = datetime.now().strftime("%Y-%m-%d")

    rows = []
    try:
        res = requests.post(f"{BASE}/attendance_data",
                            json={"start_date": today_str, "end_date": today_str})
        if res.status_code == 200:
            rows = [
                r for r in res.json().get('Attendance_Info', [])
                if str(r.get('employee_id', r.get('Employee_id', ''))) in team_ids
            ]
    except Exception as e:
        print("team_attendance_overview error:", e)

    present_count = len({str(r.get('employee_id', r.get('Employee_id', ''))) for r in rows})
    absent_count  = len(team_ids) - present_count

    # Average working hours
    total_hrs = 0.0
    for r in rows:
        try:
            h = r.get('Avg_working_hrs', '0')
            # Avg_working_hrs stored as timedelta-style string e.g. "8:00:00"
            parts = str(h).split(':')
            total_hrs += int(parts[0]) + int(parts[1]) / 60
        except Exception:
            pass
    avg_hours = round(total_hrs / present_count, 1) if present_count else 0

    return render(request, 'teamlead/team_attendance.html', {
        **session_user,
        "attendance_rows": rows,
        "present_count": present_count,
        "absent_count": absent_count,
        "avg_hours": avg_hours,
        "today": today_str,
    })


# ─────────────────────────────────────────────────────
# ATTENDANCE HISTORY
# /admin_get_attendance POST {Request_Type: Last_Month|Last_week|Last_Day, Emp_id}
#   → Clock_Info[{Date, employee_name, clock_in_time, clock_out_time,
#                  clock_in_location, Avg_working_hrs}]
# NOTE: endpoint requires a single Emp_id. For team view we loop per member
#       or use /attendance_data with date range (preferred — single call).
# Using /attendance_data POST {start_date, end_date} for team history.
# ─────────────────────────────────────────────────────
@login_required
def team_attendance_history(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, _, team_ids = get_team_members(session_user['username'])
    search    = request.GET.get('search', '').strip().lower()
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    quick     = request.GET.get('quick', '')
    today     = datetime.now().date()

    if quick == 'day':
        date_from = date_to = today.strftime("%Y-%m-%d")
    elif quick == 'week':
        date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to   = today.strftime("%Y-%m-%d")
    elif quick == 'month':
        date_from = today.replace(day=1).strftime("%Y-%m-%d")
        date_to   = today.strftime("%Y-%m-%d")

    # Default: last month if no filter set
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = today.strftime("%Y-%m-%d")

    rows = []
    try:
        res = requests.post(f"{BASE}/attendance_data",
                            json={"start_date": date_from, "end_date": date_to})
        if res.status_code == 200:
            rows = [
                r for r in res.json().get('Attendance_Info', [])
                if str(r.get('employee_id', r.get('Employee_id', ''))) in team_ids
            ]
    except Exception as e:
        print("team_attendance_history error:", e)

    if search:
        rows = [r for r in rows
                if search in str(r.get('employee_name', r.get('Employee_Name', ''))).lower()
                or search in str(r.get('employee_id', r.get('Employee_id', ''))).lower()]

    return render(request, 'teamlead/team_attendance_history.html', {
        **session_user, "rows": rows,
        "search": search, "date_from": date_from, "date_to": date_to, "quick": quick
    })


# ─────────────────────────────────────────────────────
# DAILY STATUS
# /status_data POST {start_date, end_date}
#   → daily_status_data[{Date, Employee_id, Employee_Name, Status_Update,
#                         Issues, Completed_Task, Feature_Targets}]
# For today: start_date=today, end_date=today
# ─────────────────────────────────────────────────────
@login_required
def team_daily_status(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, _, team_ids = get_team_members(session_user['username'])
    today_str   = datetime.now().strftime("%Y-%m-%d")
    date_filter = request.GET.get('date', today_str)
    search      = request.GET.get('search', '').strip().lower()

    status_data = []
    try:
        res = requests.post(f"{BASE}/status_data",
                            json={"start_date": date_filter, "end_date": date_filter})
        if res.status_code == 200:
            status_data = [
                s for s in res.json().get('daily_status_data', [])
                if str(s.get('Employee_id')) in team_ids
            ]
    except Exception as e:
        print("team_daily_status error:", e)

    if search:
        status_data = [s for s in status_data
                       if search in str(s.get('Employee_Name', '')).lower()]

    return render(request, 'teamlead/team_daily_status.html', {
        **session_user, "status_data": status_data,
        "date_filter": date_filter, "search": search, "today": today_str
    })


@login_required
def team_status_history(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, _, team_ids = get_team_members(session_user['username'])
    today     = datetime.now().date()
    date_from = request.GET.get('date_from', (today - timedelta(days=30)).strftime("%Y-%m-%d"))
    date_to   = request.GET.get('date_to',   today.strftime("%Y-%m-%d"))

    all_status = []
    try:
        res = requests.post(f"{BASE}/status_data",
                            json={"start_date": date_from, "end_date": date_to})
        if res.status_code == 200:
            all_status = [
                s for s in res.json().get('daily_status_data', [])
                if str(s.get('Employee_id')) in team_ids
            ]
    except Exception as e:
        print("team_status_history error:", e)

    # Group by employee name
    from collections import defaultdict
    grouped = defaultdict(list)
    for s in all_status:
        grouped[s.get('Employee_Name', 'Unknown')].append(s)

    return render(request, 'teamlead/team_status_history.html', {
        **session_user, "grouped": dict(grouped),
        "date_from": date_from, "date_to": date_to
    })


# ─────────────────────────────────────────────────────
# CLOCK ADJUSTMENTS
# Flask stores in ClockAdjustment table.
# No "get all" endpoint — we fetch per employee using /Get_ClockAdj or
# use /admin_get_status style. Since no bulk endpoint exists for ClockAdj,
# we use /admin_get_attendance with Last_Month per member and cross-ref.
#
# BEST AVAILABLE APPROACH: Loop over team members and call /Get_ClockAdj
# for today's date — but that only fetches ONE date's record.
#
# REAL SOLUTION: use /admin_get_attendance per employee (Last_Month) to
# detect attendance gaps (dates missing from attendance = potential adj needed).
#
# For the approval action endpoints:
# ACCEPT: /accept_req/<Employee_Id>/<Request_Type>/<Selected_Date>/<person_name>/<Employee_Name>
# REJECT: /reject_req/<Employee_Id>/<Selected_Date>/<Request_Type>/<person_name>
#
# For listing: we iterate team members and call /admin_get_status Last_Month
# then separately call /Get_ClockAdj per known date. This is expensive.
#
# Pragmatic compromise: show a message that clock adj requests are sent via
# email to the team lead; list is not available via API. Provide accept/reject
# links in the email. For the history page, query /admin_get_attendance.
# ─────────────────────────────────────────────────────
@login_required
def team_clock_adjustments(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, team_members, team_ids = get_team_members(session_user['username'])

    # Fetch last-month attendance per team member and collect ClockAdj records
    # by calling /Get_ClockAdj for dates that have ClockAdjustment entries.
    # Since there's no bulk endpoint, we gather all attendance records and
    # check for ClockAdj requests by calling /Get_ClockAdj for each member/date.
    # For performance, we limit to the last 30 days attendance dates.

    clk_requests = []
    today    = datetime.now().date()
    date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    date_to   = today.strftime("%Y-%m-%d")

    for emp in team_members:
        emp_id = str(emp.get('Employee_id'))
        try:
            # Get attendance rows for this employee
            att_res = requests.post(
                f"{BASE}/admin_get_attendance",
                json={"Request_Type": "Last_Month", "Emp_id": emp_id}
            )
            if att_res.status_code == 200:
                for row in att_res.json().get('Clock_Info', []):
                    date_str = str(row.get('Date', ''))[:10]
                    # Check if ClockAdj exists for this date
                    cadj_res = requests.post(
                        f"{BASE}/Get_ClockAdj",
                        json={"Selected_Date": date_str, "user_id": emp_id}
                    )
                    if cadj_res.status_code == 200:
                        clock_info = cadj_res.json().get('Clock_Info', [])
                        if clock_info:
                            for c in clock_info:
                                c['Employee_id']   = emp_id
                                c['Employee_Name'] = emp.get('Employee_Name')
                                c['Selected_Date'] = date_str
                                c['Request_Status'] = c.get('Request_Status', 'waiting')
                                if str(c.get('Request_Status', '')).lower() == 'waiting':
                                    clk_requests.append(c)
        except Exception as e:
            print(f"Clock adj fetch error for {emp_id}:", e)

    return render(request, 'teamlead/team_clock_adjustments.html', {
        **session_user, "clk_requests": clk_requests
    })


@login_required
def team_clock_adjust_action(request, emp_id, req_type, selected_date, person_name, emp_name):
    """
    ACCEPT: /accept_req/<Employee_Id>/<Request_Type>/<Selected_Date>/<person_name>/<Employee_Name>
    REJECT: /reject_req/<Employee_Id>/<Selected_Date>/<Request_Type>/<person_name>
    """
    action = request.GET.get('action', 'accept')
    try:
        if action == 'accept':
            requests.get(
                f"{BASE}/accept_req/{emp_id}/{req_type}/{selected_date}/{person_name}/{emp_name}"
            )
        else:
            requests.get(
                f"{BASE}/reject_req/{emp_id}/{selected_date}/{req_type}/{person_name}"
            )
    except Exception as e:
        print("Clock adj action error:", e)
    return redirect('team_clock_adjustments')


@login_required
def team_clock_adj_history(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, team_members, team_ids = get_team_members(session_user['username'])
    req_type  = request.GET.get('req_type', 'All')
    status    = request.GET.get('status', 'All')
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    today     = datetime.now().date()

    if not date_from:
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = today.strftime("%Y-%m-%d")

    history = []
    for emp in team_members:
        emp_id = str(emp.get('Employee_id'))
        try:
            att_res = requests.post(
                f"{BASE}/admin_get_attendance",
                json={"Request_Type": "Last_Month", "Emp_id": emp_id}
            )
            if att_res.status_code == 200:
                for row in att_res.json().get('Clock_Info', []):
                    date_str = str(row.get('Date', ''))[:10]
                    cadj_res = requests.post(
                        f"{BASE}/Get_ClockAdj",
                        json={"Selected_Date": date_str, "user_id": emp_id}
                    )
                    if cadj_res.status_code == 200:
                        for c in cadj_res.json().get('Clock_Info', []):
                            c['Employee_id']   = emp_id
                            c['Employee_Name'] = emp.get('Employee_Name')
                            c['Selected_Date'] = date_str
                            history.append(c)
        except Exception as e:
            print(f"Clock adj history error for {emp_id}:", e)

    if req_type != 'All':
        history = [c for c in history if c.get('Request_Type') == req_type]
    if status != 'All':
        history = [c for c in history
                   if str(c.get('Request_Status', '')).lower() == status.lower()]
    if date_from:
        history = [c for c in history if c.get('Selected_Date', '') >= date_from]
    if date_to:
        history = [c for c in history if c.get('Selected_Date', '') <= date_to]

    return render(request, 'teamlead/team_clock_adj_history.html', {
        **session_user, "history": history,
        "req_type": req_type, "status": status,
        "date_from": date_from, "date_to": date_to
    })


# ─────────────────────────────────────────────────────
# QUERIES
# /Queries_Info POST {employee_id, request: "all"}
#   → Queries_Info[{query_id, Employee_id, Employee_Name, Date, Time, Query, Status, Reply}]
# /reply_query  POST {query_id, answer}
# /query        POST {Employee_id, Employee_Name, Employee_Email, Query}
# /employee_queries POST {employee_id} → Queries_Info[{query_id, Date, Time, Query, Status, Reply}]
# ─────────────────────────────────────────────────────
@login_required
def team_queries(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    _, _, team_ids = get_team_members(session_user['username'])

    queries = []
    try:
        # Get all queries, filter to team members
        res = requests.post(f"{BASE}/Queries_Info",
                            json={"employee_id": "", "request": "all"})
        if res.status_code == 200:
            queries = [
                q for q in res.json().get('Queries_Info', [])
                if str(q.get('Employee_id')) in team_ids
            ]
    except Exception as e:
        print("team_queries error:", e)

    return render(request, 'teamlead/team_queries.html', {
        **session_user, "queries": queries
    })


@login_required
def reply_query(request, query_id):
    """
    /reply_query POST {query_id, answer}
    """
    if request.method == "POST":
        answer = request.POST.get("reply", "").strip()
        if answer:
            try:
                requests.post(f"{BASE}/reply_query",
                              json={"query_id": query_id, "answer": answer})
            except Exception as e:
                print("reply_query error:", e)
    return redirect('team_queries')


@login_required
def teamlead_my_queries(request):
    """
    Submit: /query POST {Employee_id, Employee_Name, Employee_Email, Query}
    View:   /employee_queries POST {employee_id} → Queries_Info
    """
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    emp_id    = session_user.get('user_id', '')
    emp_name  = session_user.get('username', '')
    emp_email = session_user.get('email', '')
    success   = False
    my_queries = []

    if request.method == "POST":
        query_text = request.POST.get("query", "").strip()
        if query_text:
            try:
                requests.post(f"{BASE}/query", json={
                    "Employee_id":    emp_id,
                    "Employee_Name":  emp_name,
                    "Employee_Email": emp_email,
                    "Query":          query_text,
                })
                success = True
            except Exception as e:
                print("Submit query error:", e)

    try:
        res = requests.post(f"{BASE}/employee_queries",
                            json={"employee_id": emp_id})
        if res.status_code == 200:
            my_queries = res.json().get('Queries_Info', [])
    except Exception as e:
        print("employee_queries fetch error:", e)

    return render(request, 'teamlead/teamlead_my_queries.html', {
        **session_user, "my_queries": my_queries, "success": success
    })


# ─────────────────────────────────────────────────────
# ANNOUNCEMENTS
# /Announcement_Info POST {}
#   → Announcement_Info[{Employee_Name, Announcement, Announcement_date}]
# ─────────────────────────────────────────────────────
@login_required
def team_announcements(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    announcements = []
    try:
        res = requests.post(f"{BASE}/Announcement_Info", json={})
        if res.status_code == 200:
            announcements = res.json().get('Announcement_Info', [])
    except Exception as e:
        print("team_announcements error:", e)

    return render(request, 'teamlead/team_announcements.html', {
        **session_user, "announcements": announcements
    })


# ─────────────────────────────────────────────────────
# TEAM DASHBOARD (tabbed)
# ─────────────────────────────────────────────────────
@login_required
def team_dashboard(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    team_lead_name = session_user['username']
    tab = request.GET.get("tab", "leave")
    _, team_members, team_ids = get_team_members(team_lead_name)
    today_str = datetime.now().strftime("%Y-%m-%d")
    today     = datetime.now().date()

    leave_data = attendance_data = wfh_data = status_data = []

    if tab == "leave":
        try:
            res = requests.post(f"{BASE}/get_all_leaves_summary", json={})
            if res.status_code == 200:
                leave_data = [lv for lv in res.json().get('all_leaves', [])
                              if str(lv.get('Employee_id')) in team_ids]
        except Exception as e:
            print("tab leave error:", e)

    elif tab == "attendance":
        date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        try:
            res = requests.post(f"{BASE}/attendance_data",
                                json={"start_date": date_from, "end_date": today_str})
            if res.status_code == 200:
                attendance_data = [
                    r for r in res.json().get('Attendance_Info', [])
                    if str(r.get('employee_id', r.get('Employee_id', ''))) in team_ids
                ]
        except Exception as e:
            print("tab attendance error:", e)

    elif tab == "wfh":
        try:
            res = requests.post(f"{BASE}/get_employees_count", json={})
            if res.status_code == 200:
                wfh_data = [w for w in res.json().get('Work_From_Home_Info', [])
                            if str(w.get('Employee_id')) in team_ids]
        except Exception as e:
            print("tab wfh error:", e)

    elif tab == "status":
        date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        try:
            res = requests.post(f"{BASE}/status_data",
                                json={"start_date": date_from, "end_date": today_str})
            if res.status_code == 200:
                status_data = [s for s in res.json().get('daily_status_data', [])
                               if str(s.get('Employee_id')) in team_ids]
        except Exception as e:
            print("tab status error:", e)

    # KPI counts
    present_today = 0
    try:
        res = requests.post(f"{BASE}/get_all_attendance_summary", json={})
        if res.status_code == 200:
            present_today = sum(
                1 for r in res.json().get('all_rows', [])
                if str(r.get('Date', ''))[:10] == today_str
                and str(r.get('employee_id')) in team_ids
            )
    except: pass

    pending_leaves = 0
    try:
        res = requests.post(f"{BASE}/get_all_leaves_summary", json={})
        if res.status_code == 200:
            pending_leaves = sum(
                1 for lv in res.json().get('all_leaves', [])
                if lv.get('Status') == 'Waiting'
                and str(lv.get('Employee_id')) in team_ids
            )
    except: pass

    pending_wfh = 0
    try:
        res = requests.post(f"{BASE}/get_employees_count", json={})
        if res.status_code == 200:
            pending_wfh = sum(
                1 for w in res.json().get('Work_From_Home_Info', [])
                if w.get('Status') == 'Waiting'
                and str(w.get('Employee_id')) in team_ids
            )
    except: pass

    return render(request, "teamlead/team_dashboard.html", {
        **session_user, "tab": tab, "team_members": team_members,
        "leave_data": leave_data, "attendance_data": attendance_data,
        "wfh_data": wfh_data, "status_data": status_data,
        "total_team": len(team_members), "present_today": present_today,
        "pending_leaves": pending_leaves, "pending_wfh": pending_wfh,
    })


# ─────────────────────────────────────────────────────
# OWN ATTENDANCE (Team lead self clock-in/out)
# /clock_in POST {employee_id, employee_name, historic, district, button_name}
#   button_name: "clock_in" | "clock_out"
# /get_clock_in POST {employee_id} → current_time, Profile_Info
# /get_employee_attendance POST {employee_id}
#   → employee_clock_info[{Date, clock_in_time, clock_out_time, Avg_working_hrs}]
# ─────────────────────────────────────────────────────
@login_required
def teamlead_own_attendance(request):
    session_user = get_session_user(request)
    if _tl_only(request, session_user):
        return redirect('home')

    emp_id   = session_user.get('user_id', '')
    emp_name = session_user.get('username', '')
    today_str = datetime.now().strftime("%Y-%m-%d")
    message = ""

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action in ("clock_in", "clock_out"):
            try:
                res = requests.post(f"{BASE}/clock_in", json={
                    "employee_id":   emp_id,
                    "employee_name": emp_name,
                    "historic":      "Office",   # default location
                    "district":      "HQ",
                    "button_name":   action,      # "clock_in" or "clock_out"
                })
                data = res.json()
                message = data.get('message', 'Done.')
            except Exception as e:
                print("clock action error:", e)
                message = "Action failed. Please try again."

    # Today's record
    today_record = None
    attendance_history = []
    try:
        res = requests.post(f"{BASE}/get_employee_attendance",
                            json={"employee_id": emp_id})
        if res.status_code == 200:
            attendance_history = res.json().get('employee_clock_info', [])
            for row in attendance_history:
                if str(row.get('Date', ''))[:10] == today_str:
                    today_record = row
                    break
    except Exception as e:
        print("own attendance fetch error:", e)

    return render(request, 'teamlead/teamlead_own_attendance.html', {
        **session_user,
        "today_record":       today_record,
        "attendance_history": attendance_history,
        "today":              today_str,
        "message":            message,
    })

@login_required
def teamlead_analytics(request):
    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    if session_user['user_type'].lower() != 'teamlead':
        return HttpResponse("Unauthorized", status=403)

    import json
    from collections import Counter
    from datetime import datetime, timedelta

    # ── Period ────────────────────────────────────────────────────
    # BUG 3 FIX: period was never passed to context — now it is.
    try:
        period = int(request.GET.get('period', 30))
    except (ValueError, TypeError):
        period = 30

    cutoff = (datetime.now() - timedelta(days=period)).strftime("%Y-%m-%d")

    # ── STEP 1: GET TEAM MEMBERS ──────────────────────────────────
    # BUG 1 FIX: removed hardcoded TEAMLEAD_MAP — use session username
    # directly, same as every other teamlead view in this file.
    team_lead_name = session_user.get('username')
    _, team_members, team_ids = get_team_members(team_lead_name)

    total_employees = len(team_members)

    # ── STEP 2: ATTENDANCE ────────────────────────────────────────
    attendance_summary = []
    daily_attendance   = []
    monthly_top        = []
    monthly_bottom     = []

    try:
        r    = requests.post("http://localhost:5000/get_all_attendance_summary", json={})
        data = r.json()

        # Per-employee summary filtered to this team + period
        name_days = {}
        for row in data.get('summary', []):
            if str(row.get('Employee_id')) in team_ids:
                attendance_summary.append({
                    'employee_id':   row.get('Employee_id'),
                    'employee_name': row.get('Employee_Name'),
                    'present_days':  int(row.get('present_days', 0)),
                })
                name_days[row.get('Employee_Name', '')] = int(row.get('present_days', 0))

        # Daily attendance trend (filtered by period cutoff)
        daily_map = Counter()
        for rec in data.get('all_rows', []):
            if str(rec.get('employee_id')) in team_ids:
                d = str(rec.get('Date', ''))[:10]
                if d and d >= cutoff:
                    daily_map[d] += 1

        daily_attendance = [
            {'date': k, 'count': v}
            for k, v in sorted(daily_map.items())
        ]

        # Monthly top / bottom (group by YYYY-MM)
        monthly_map = {}
        for rec in data.get('all_rows', []):
            if str(rec.get('employee_id')) in team_ids:
                d = str(rec.get('Date', ''))[:10]
                if not d:
                    continue
                ym = d[:7]   # "2025-03"
                emp_name = rec.get('employee_name') or rec.get('Employee_Name', '')
                emp_id   = str(rec.get('employee_id', ''))
                monthly_map.setdefault(ym, {})
                key = emp_id or emp_name
                entry = monthly_map[ym].setdefault(key, {'name': emp_name, 'id': emp_id, 'days': 0})
                entry['days'] += 1

        for ym, emp_dict in sorted(monthly_map.items()):
            sorted_emps = sorted(emp_dict.values(), key=lambda x: x['days'], reverse=True)
            month_label = ym   # e.g. "2025-03"
            try:
                month_label = datetime.strptime(ym, "%Y-%m").strftime("%b %Y")
            except Exception:
                pass
            monthly_top.append({
                'month': month_label,
                'list':  sorted_emps[:10]
            })
            monthly_bottom.append({
                'month': month_label,
                'list':  list(reversed(sorted_emps))[:10]
            })

    except Exception as e:
        print("Attendance error:", e)

    # ── STEP 3: LEAVES ────────────────────────────────────────────
    leave_requests = []
    leave_status   = {}

    try:
        r          = requests.post("http://localhost:5000/get_all_leaves_summary", json={})
        all_leaves = r.json().get('all_leaves', [])

        for l in all_leaves:
            if str(l.get('Employee_id')) in team_ids:
                leave_requests.append(l)

        # BUG 5 FIX: normalise status labels so the chart works
        status_counter = Counter()
        for l in leave_requests:
            raw = l.get('Status', 'Pending')
            if raw == 'Waiting':
                raw = 'Pending'
            status_counter[raw] += 1

        leave_status = dict(status_counter)

    except Exception as e:
        print("Leave error:", e)

    # ── STEP 4: WFH ───────────────────────────────────────────────
    wfh_summary  = []
    wfh_requests = []
    wfh_status   = {}
    wfh_today    = 0
    today_str    = datetime.now().strftime("%Y-%m-%d")

    try:
        r    = requests.post("http://localhost:5000/get_employees_count", json={})
        data = r.json()

        wfh_counter = Counter()
        for w in data.get('Work_From_Home_Info', []):
            if str(w.get('Employee_id')) not in team_ids:
                continue

            raw_status = w.get('Status', 'Waiting')
            # Normalise
            norm = 'Accepted' if raw_status == 'Accepted' else (
                   'Rejected' if raw_status == 'Rejected' else 'Pending')

            wfh_counter[norm] += 1
            wfh_requests.append({
                'Employee_Name': w.get('Employee_Name'),
                'Employee_id':   w.get('Employee_id'),
                'Status':        norm,
                'Start_Date':    str(w.get('Start_Date', ''))[:10],
                'End_Date':      str(w.get('End_Date', ''))[:10],
                'Reason':        w.get('Reason', ''),
            })

            start = str(w.get('Start_Date', ''))[:10]
            end   = str(w.get('End_Date', ''))[:10]
            if norm == 'Accepted' and start and end and start <= today_str <= end:
                wfh_today += 1
                wfh_summary.append({
                    'Employee_Name': w.get('Employee_Name'),
                    'Employee_id':   w.get('Employee_id'),
                    'wfh_days':      1,
                })

        # BUG 5 FIX: populate wfh_status so the Leave Status Split chart works
        wfh_status = dict(wfh_counter)

    except Exception as e:
        print("WFH error:", e)

    # ── FINAL CONTEXT ─────────────────────────────────────────────
    # BUG 2 FIX: template path lowercase 'teamlead/' not 'TeamLead/'
    # BUG 3 FIX: period now in context
    context = {
        **session_user,
        'period':                  period,
        'total_employees':         total_employees,

        'all_employees_json':      json.dumps(team_members),
        'leave_requests_json':     json.dumps(leave_requests),
        'attendance_summary_json': json.dumps(attendance_summary),
        'daily_attendance_json':   json.dumps(daily_attendance),
        'wfh_summary_json':        json.dumps(wfh_summary),
        'wfh_requests_json':       json.dumps(wfh_requests),
        'wfh_status_json':         json.dumps(wfh_status),
        'wfh_today':               wfh_today,
        'leave_status_json':       json.dumps(leave_status),

        # BUG 4 FIX: monthly top/bottom now computed from real data
        'monthly_top_json':        json.dumps(monthly_top),
        'monthly_bottom_json':     json.dumps(monthly_bottom),
    }

    # BUG 2 FIX: lowercase path matches actual template folder name
    return render(request, 'teamlead/teamlead_analytics.html', context)