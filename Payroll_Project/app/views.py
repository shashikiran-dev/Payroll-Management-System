from django.shortcuts import render,redirect
from jupyter_core.version import parts
import requests
import json
from django.http import JsonResponse,HttpResponse
import random
from django.core.mail import send_mail
from datetime import datetime
from .models import Registration
from payroll import settings
from django.template.loader import get_template
# from xhtml2pdf import pisa
from openpyxl import Workbook
from io import BytesIO
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict

# Create your views here.
# DJANGO
import json
import requests

#session-protection decorator
def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('Authenticated'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

#helper to read session data
def get_session_user(request):
    return {
        "username": request.session.get('username'),
        "email": request.session.get('user_email'),
        "user_type": request.session.get('user_type'),
        "user_id": request.session.get('user_id'),
        "Team_lead_email": request.session.get('Team_lead_email'),
    }


def user_login(request):
    if request.method == 'POST':

        # remove old session -change
        request.session.flush()

        email = request.POST.get('email')
        password = request.POST.get('password')
        usertype = request.POST.get('role')
        print(email,password,usertype)

        response = requests.post(
            "http://localhost:5000/login",
            json={
                "username": email,
                "password": password,
                "usertype": usertype
            }
        )

        flask_data = response.json()
        print("DJANGO → FLASK:", flask_data)

        if flask_data.get('status') == 'success':
            #before
            #request.session['username'] = 'Diwakar'
            #request.session['user_type'] = 'Employer'
            
            request.session['Authenticated'] = True
            request.session['username'] = flask_data['username']
            # after completly new session-change
            request.session['user_id'] = flask_data['user_id']
            request.session['user_email'] = flask_data['employee_email']
            request.session['user_type'] = flask_data['user_type'].lower()

            request.session.modified = True

            print(" FINAL SESSION:", dict(request.session))

            return redirect('home')

        return render(request, 'login.html', {'failed': 'Invalid credentials'})

    return render(request, 'login.html')

# def register(request):
#     if request.method == "POST":
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         confpass = request.POST.get('confpass')
#         email = request.POST.get('email')
#         usertype = request.POST.get('role')

#         print(username, email, usertype, password, confpass)

#         #  validation
#         if not all([username, email, password, confpass, usertype]):
#             return render(request, 'register.html', {
#                 'error': 'All fields are required'
#             })

#         if password != confpass:
#             return render(request, 'register.html', {
#                 'error': 'Passwords do not match'
#             })

#         data = {
#             "username": username,
#             "email": email,
#             "usertype": usertype,
#             "password": password
#         }

#         flask_url = "http://localhost:5000/data_receive"
#         response = requests.post(flask_url, json=data)

#         if response.status_code != 200:
#             return render(request, 'register.html', {
#                 'error': 'Server error. Please try again.'
#             })

#         flask_response_data = response.json()
#         print("Flask response:", flask_response_data)

#         #  Handle Flask failure (duplicate email etc.)
#         if flask_response_data.get('status') != 'success':
#             return render(request, 'register.html', {
#                 'error': flask_response_data.get(
#                     'message',
#                     'Registration failed'
#                 )
#             })

#         # SUCCESS → redirect to login
#         return redirect('login')

#     return render(request, 'register.html')

# def forgot_password(request):
#     return render(request,'forgot.html')

@login_required
def home(request):
    context = {
        'username': request.session.get('username'),
        'email': request.session.get('user_email'),
        'user_id': request.session.get('user_id'),
        'user_type': request.session.get('user_type'),
    }

    if context['user_type'].lower() == "employer":
        return redirect('admin_analytics')
    elif context["user_type"].lower() == "teamlead":
        return redirect('team_dashboard')
    return redirect('clock')

def logout(request):
    request.session.flush()
    return redirect('login')

def forgot(request):
    return render(request,'forgot_password.html')

def forgot_password(request):
    global OtpNumber
    global Forgot_UserData
    global Forgot_UserName
    global email
    email=""
    if request.method == 'POST':
        email=request.POST['email']
        try:
            data={
            "email":email
            }
            print(data)
            flask_url="http://localhost:5000/validate_email"
            response=requests.post(flask_url,json=data)
            flask_response=response.json()
            print(flask_response['status'])
            if flask_response['status']:
                validate_password(request,"otpenter",email)
            else:
                print("error coming",response.status_code)
        except Exception as e:
            print("error is occures")
    if email:
        return render(request,'forgot.html',{"email":email,"name":"sudhakar"})
    return render(request,'forgot.html')



def validate_password(request, keyword):

    # ================= OTP GENERATION =================
    if keyword == 'otpenter':
        email = request.session.get('reset_email')

        if not email:
            return redirect('forgot_password')

        otp = random.randint(100000, 999999)

        # ✅ STORE OTP IN SESSION
        request.session['reset_otp'] = otp

        subject = 'Password Reset OTP'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        message = f"""
Your password reset request is approved.

Your 6-digit OTP is: {otp}

Do not share this OTP with anyone.
"""

        send_mail(subject, message, from_email, recipient_list)

        return render(request, 'forgot.html', {
            'step': 'otp_sent'
        })

    # ================= OTP VALIDATION =================
    if keyword == 'otpvalidate' and request.method == 'POST':

        otp_entered = request.POST.get('input1')
        new_password = request.POST.get('input2')
        confirm_password = request.POST.get('input3')

        session_otp = request.session.get('reset_otp')
        email = request.session.get('reset_email')

        if not session_otp or not email:
            return redirect('forgot_password')

        if new_password != confirm_password:
            return render(request, 'forgot.html', {
                'error': 'Passwords do not match'
            })

        if int(otp_entered) != session_otp:
            return render(request, 'forgot.html', {
                'error': 'Invalid OTP'
            })

        # ✅ OTP VALID → UPDATE PASSWORD IN FLASK
        data = {
            'email': email,
            'password': new_password
        }

        flask_url = "http://localhost:5000/update_password"
        response = requests.post(flask_url, json=data)

        if response.status_code == 200:
            # 🔥 CLEAR RESET SESSION
            request.session.pop('reset_otp', None)
            request.session.pop('reset_email', None)

            return redirect('login')

        return render(request, 'forgot.html', {
            'error': 'Password update failed'
        })

    return redirect('forgot_password')
@login_required
def clock(request):
    session_user = get_session_user(request)

    user_id   = session_user['user_id']
    user_type = session_user['user_type']

    if user_type.lower() == 'employer':
        return redirect('home')

    # 1. Clock-in data (existing)
    flask_url     = "http://localhost:5000/get_clock_in"
    response      = requests.post(flask_url, json={"employee_id": user_id})
    response_data = response.json()

    # 2. Attendance history for calendar dots
    Attendance_data = []
    try:
        att_resp = requests.post(
            "http://localhost:5000/get_attendance_data",
            json={"request_type": "all_data", "username": session_user['username'],
                  "id": user_id, "start_date": None, "end_date": None}
        )
        if att_resp.status_code == 200:
            raw = att_resp.json().get('Attendance_data', [])
            def safe_fmt(val):
                if not val: return val
                for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
                    except ValueError: continue
                return val
            for r in raw:
                r['Date'] = safe_fmt(r.get('Date', ''))
            Attendance_data = raw
    except Exception as e:
        print("Attendance fetch error:", e)

    # 3. Public holidays for calendar
    Holidays_Data = []
    try:
        fest_resp = requests.post("http://localhost:5000/fest_info",
                                  json={"employee_id": user_id})
        if fest_resp.status_code == 200:
            raw_h = fest_resp.json().get('holiday_info', [])
            def safe_date(val):
                if not val: return val
                for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
                    except ValueError: continue
                return val
            for h in raw_h:
                h['Date'] = safe_date(h.get('Holiday_date') or h.get('Date', ''))
            Holidays_Data = raw_h
    except Exception as e:
        print("Holiday fetch error:", e)

    context = {
        **session_user,
        "Profile_Info":    response_data.get("Profile_Info"),
        "current_time":    response_data.get("current_time"),
        "Attendance_data": Attendance_data,
        "Holidays_Data":   Holidays_Data,
    }
    return render(request, 'user/clock.html', context)
#-------------------------------------Admin analytics Dashboard----------------------------------------
import json
from datetime import date, timedelta

@login_required
def admin_analytics(request):
    session_user = get_session_user(request)
    if not session_user:
        return redirect('login')
    if session_user['user_type'].lower() != 'employer':
        return HttpResponse("Unauthorized", status=403)

    period = int(request.GET.get('period', 30))

    from collections import Counter, defaultdict

    # ── JSON-safe serializer: converts ALL Python types to strings ──
    def make_serializable(obj):
        """Recursively convert any non-JSON-safe types in dicts/lists."""
        if isinstance(obj, list):
            return [make_serializable(i) for i in obj]
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, date):          # datetime.date and datetime.datetime
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, timedelta):     # timedelta → HH:MM:SS string
            total = int(obj.total_seconds())
            h, rem = divmod(abs(total), 3600)
            m, s   = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"
        if obj is None:
            return ''
        return obj

    def safe_date(val):
        if not val: return ''
        if isinstance(val, date): return val.strftime("%Y-%m-%d")
        for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d"):
            try: return datetime.strptime(str(val), fmt).strftime("%Y-%m-%d")
            except: continue
        return str(val)

    total_employees    = 0
    all_employees      = []
    leave_requests     = []
    wfh_summary        = []
    attendance_summary = []
    daily_attendance   = []
    wfh_today          = 0
    leave_status       = {}

    # ── Step 1: Employee list + ALL WFH records ─────────────
    raw_wfh = []
    wfh_status_counts = {'Pending': 0, 'Accepted': 0, 'Rejected': 0}
    try:
        r1 = requests.post(
            "http://localhost:5000/get_employees_count",
            json={"request_type": "get_employess"},
            timeout=10
        )
        if r1.status_code == 200:
            d1 = r1.json()
            total_employees = d1.get('Total_employees', [{}])[0].get('COUNT(Employee_id)', 0)
            all_employees   = d1.get('all_employee_name_id', [])

            today_str = datetime.now().strftime("%Y-%m-%d")
            for w in d1.get('Work_From_Home_Info', []):
                start      = safe_date(w.get('Start_Date', ''))
                end        = safe_date(w.get('End_Date', ''))
                raw_status = w.get('Status', 'Waiting')
                # Normalise status labels for analytics charts
                if raw_status == 'Waiting':
                    norm_status = 'Pending'
                elif raw_status == 'Accepted':
                    norm_status = 'Accepted'
                elif raw_status == 'Rejected':
                    norm_status = 'Rejected'
                else:
                    norm_status = raw_status

                raw_wfh.append({
                    'Employee_Name': w.get('Employee_Name', ''),
                    'Employee_id':   w.get('Employee_id', ''),
                    'Start_Date':    start,
                    'End_Date':      end,
                    'No_of_Days':    w.get('No_of_Days', ''),
                    'Reason':        w.get('Reason', ''),
                    'Applied_on':    safe_date(w.get('Applied_on', '')),
                    'Status':        norm_status,
                })
                if norm_status in wfh_status_counts:
                    wfh_status_counts[norm_status] += 1
                # Count who is actively WFH today (Accepted + date range covers today)
                if norm_status == 'Accepted' and start and end and start <= today_str <= end:
                    wfh_today += 1
    except Exception as e:
        print("Step1 error:", e)

    # WFH summary per employee (accepted days only)
    wfh_map = defaultdict(lambda: {'Employee_Name':'','wfh_days':0,'office_days':0})
    for w in raw_wfh:
        key = w['Employee_id'] or w['Employee_Name']
        wfh_map[key]['Employee_Name'] = w['Employee_Name']
        if w['Status'] == 'Accepted':
            wfh_map[key]['wfh_days'] += 1
    wfh_summary = list(wfh_map.values())

    # ── Step 2: ALL leaves from both Leave_Request + Leave_history ──
    # Uses /get_all_leaves_summary which fetches both pending and historical leaves
    try:
        r2 = requests.post(
            "http://localhost:5000/get_all_leaves_summary",
            json={},
            timeout=10
        )
        if r2.status_code == 200:
            raw_all = make_serializable(r2.json().get('all_leaves', []))
            for l in raw_all:
                # Normalise status: DB stores 'Waiting','Accepted','Rejected'
                raw_status = l.get('Status') or 'Waiting'
                if raw_status == 'Waiting':
                    norm_status = 'Pending'
                elif raw_status == 'Accepted':
                    norm_status = 'Approved'
                else:
                    norm_status = raw_status   # Rejected stays as-is

                leave_requests.append({
                    'Employee_Name': l.get('Employee_Name', ''),
                    'Employee_id':   l.get('Employee_id', ''),
                    'Leave_type':    l.get('Leave_Type') or l.get('Leave_type') or '',
                    'Start_date':    safe_date(l.get('Start_date', '')),
                    'End_date':      safe_date(l.get('End_date', '')),
                    'No_of_days':    l.get('No_of_Days') or l.get('No_of_days') or '',
                    'Status':        norm_status,
                    'Applied_on':    safe_date(l.get('Applied_on', '')),
                })
    except Exception as e:
        print("Leave summary error:", e)

    # leave_status counts: {'Pending': N, 'Approved': N, 'Rejected': N}
    leave_status = dict(Counter(l['Status'] for l in leave_requests))

    # ── Step 3: ALL attendance in ONE bulk request ──────────────
    daily_date_list = []
    month_attendance = defaultdict(lambda: defaultdict(lambda: {'name': '', 'days': 0}))

    try:
        r3 = requests.post(
            "http://localhost:5000/get_all_attendance_summary",
            json={},
            timeout=30
        )
        if r3.status_code == 200:
            r3_data = r3.json()
            for row in r3_data.get('summary', []):
                attendance_summary.append({
                    'employee_id':   row.get('Employee_id', ''),
                    'employee_name': row.get('Employee_Name', ''),
                    'present_days':  int(row.get('present_days', 0)),
                    'absent_days':   None,
                })
            for rec in r3_data.get('all_rows', []):
                d      = rec.get('Date', '')
                emp_id = rec.get('employee_id', '')
                emp_nm = rec.get('employee_name', '')
                if not d:
                    continue
                d = safe_date(d) or d
                daily_date_list.append(d)
                month_key = d[:7]
                month_attendance[month_key][emp_id]['name'] = emp_nm
                month_attendance[month_key][emp_id]['days'] += 1
        else:
            print(f"Attendance bulk failed: {r3.status_code}")
    except Exception as e:
        print("Attendance bulk error:", e)
        for emp in all_employees:
            attendance_summary.append({
                'employee_id':   emp.get('Employee_id', ''),
                'employee_name': emp.get('Employee_Name', ''),
                'present_days':  0,
                'absent_days':   None,
            })

    attendance_summary.sort(key=lambda x: x['present_days'], reverse=True)

    # Build per-month top/bottom attendance lists for the UI panels
    monthly_top    = []   # [{month, top_name, top_days, top_list:[{name,days}]}]
    monthly_bottom = []   # [{month, bottom_name, bottom_days, bottom_list:[...]}]
    for month_key in sorted(month_attendance.keys(), reverse=True):
        emp_data = month_attendance[month_key]
        ranked = sorted(
            [{'id': k, 'name': v['name'], 'days': v['days']} for k, v in emp_data.items()],
            key=lambda x: x['days'], reverse=True
        )
        if ranked:
            import calendar
            try:
                y, m = map(int, month_key.split('-'))
                month_label = f"{calendar.month_name[m]} {y}"
            except:
                month_label = month_key
            monthly_top.append({
                'month': month_label,
                'month_key': month_key,
                'top_name': ranked[0]['name'],
                'top_days': ranked[0]['days'],
                'list': ranked[:10]  # top 10
            })
            monthly_bottom.append({
                'month': month_label,
                'month_key': month_key,
                'bottom_name': ranked[-1]['name'],
                'bottom_days': ranked[-1]['days'],
                'list': ranked[-10:][::-1]  # bottom 10, worst first
            })

    daily_counts     = Counter(daily_date_list)
    daily_attendance = [{'date': d, 'count': c} for d, c in sorted(daily_counts.items())]

    print(f"ANALYTICS DONE → emps:{total_employees} leaves:{len(leave_requests)} wfh:{len(wfh_summary)} att:{len(attendance_summary)} daily:{len(daily_attendance)}")

    # ── Serialize everything to JSON strings for safe template injection ──
    context = {
        **session_user,
        'total_employees':        total_employees,
        'period':                 period,
        # These are passed as JSON strings — template uses |safe on them
        'all_employees_json':     json.dumps(make_serializable(all_employees)),
        'leave_requests_json':    json.dumps(make_serializable(leave_requests)),
        'attendance_summary_json':json.dumps(make_serializable(attendance_summary)),
        'daily_attendance_json':  json.dumps(make_serializable(daily_attendance)),
        'monthly_top_json':       json.dumps(make_serializable(monthly_top)),
        'monthly_bottom_json':    json.dumps(make_serializable(monthly_bottom)),
        'wfh_summary_json':       json.dumps(make_serializable(wfh_summary)),
        'wfh_requests_json':      json.dumps(make_serializable(raw_wfh)),
        'wfh_status_json':        json.dumps(make_serializable(wfh_status_counts)),
        'wfh_today':              wfh_today,
        'leave_status_json':      json.dumps(make_serializable(leave_status)),
    }
    return render(request, 'Admin/analytics.html', context)



@login_required
def attendance_data(request):
    user = get_session_user(request)

    start = request.POST.get('start_date')
    end = request.POST.get('end_date')

    data = {
        "request_type": "all_data",
        "username": user['username'],
        "id": user['user_id'],
        "start_date": start,
        "end_date": end,
    }

    flask_url = "http://localhost:5000/get_attendance_data"
    response = requests.post(flask_url, json=data)

    Attendance_data = []

    if response.status_code == 200:
        response_data = response.json()
        print("response data from attendance is", response_data)

        Attendance_data = response_data.get('Attendance_data', [])

        # ✅ Normalize date format
        for row in Attendance_data:
            try:
                input_date = datetime.strptime(
                    row['Date'],
                    "%a, %d %b %Y %H:%M:%S %Z"
                )
                row['Date'] = input_date.strftime("%Y-%m-%d")
            except Exception:
                pass

    return render(
        request,
        'user/clock.html',
        {
            **user,
            "Attendance_data": Attendance_data
        }
    )

@login_required
def get_specific_data(request):
    session_user = get_session_user(request)

    username = session_user['username']
    email = session_user['email']
    user_type = session_user['user_type']
    user_id = session_user['user_id']

    print("get_specific_data called for:", username, user_id)

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        print("dates are", start_date, end_date)

        data = {
            "start_date": start_date,
            "end_date": end_date,
            "username": username,
            "id": user_id,
            "request_type": "between_dates"
        }

        flask_url = "http://localhost:5000/get_attendance_data"
        response = requests.post(flask_url, json=data)

        if response.status_code == 200:
            response_data = response.json()
            Attendance_data = response_data.get('Attendance_data', [])

            
            return render(
                request,
                'user/clock.html',
                {
                    **session_user,
                    "Attendance_data": Attendance_data
                }
            )

    return render(
        request,
        'user/clock.html',
        session_user
    )

# def Pdf_Download(request,username,user_type,email,user_id,start_date,end_date):
#     print("#############",username,user_type,email,user_id,start_date,end_date)
#     print("@@@",start_date)
#     data={
#             'employeeid':user_id,
#             "start_date":start_date,
#             "end_date":end_date,
#             "request_type":"in_between_dates"
#             }
#     flask_url="http://localhost:5000/get_status_update_data"
#     response=requests.post(flask_url,json=data)
#     flask_response=response.json()
#     print(flask_response)
#     if response.status_code==200:
#         print(flask_response['request_data'])
#         Entire_data=flask_response['request_data']
#         template_path = 'Status_Pdf.html'
#         context = {'my_variable': Entire_data}  # Example context data for your template
    
#     # Load template
#         template = get_template(template_path)
#         html = template.render(context)
    
#     # Create a PDF document
#         response = HttpResponse(content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename="downloaded_pdf.pdf"'
    
#     # Generate PDF
#         pisa_status = pisa.CreatePDF(html, dest=response)
    
#     # Return the response
#         if pisa_status.err:
#             return HttpResponse('We had some errors <pre>' + html + '</pre>')
#         return response
#     return HttpResponse("success")

def generate_excel(request, username, user_type, email, user_id, start_date, end_date):
    print("#############",username,user_type,email,user_id,start_date,end_date)
    # Prepare data to send to Flask endpoint
    data = {
        'employeeid': user_id,
        'start_date': start_date,
        'end_date': end_date,
        'request_type': 'in_between_dates'
    }
    
    # Flask endpoint URL
    flask_url = "http://localhost:5000/get_status_update_data"
    
    # Make a POST request to the Flask endpoint
    response = requests.post(flask_url, json=data)
    
    # Check if request was successful
    if response.status_code == 200:
        # Extract data from Flask response
        flask_response = response.json()
    
        entire_data = flask_response['request_data']
        rendered_html = render_to_string('Status_Excel.html', {'my_variable': entire_data})
        # print(entire_data[0]['Date'])
        # Initialize Excel workbook and sheet
        workbook = Workbook()
        sheet = workbook.active
        
        # Write header row
        sheet.append(['Date', 'StatusUpdate', 'Issues', 'CompletedTasks', 'FeatureTargets'])
        
        # Iterate over data and write rows
        for item in entire_data:
            sheet.append([
            item['Date'],
            item['Status_Update'],
            item['Issues'],  # Ensure to handle missing keys gracefully
            item['Completed_Task'],
            item['Feature_Targets']
        ])
        
        # Save workbook to BytesIO buffer
        excel_data = BytesIO()
        workbook.save(excel_data)
        excel_data.seek(0)
        
        # Prepare response as an Excel file download
        response = HttpResponse(
            excel_data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=data.xlsx'
        
        return response
    
    # Handle case where Flask endpoint returned an error
    else:
        return HttpResponse('Error while fetching data from Flask endpoint', status=response.status_code)

def statusCheck(request):
    if request.method=='POST':
        # empid=request.POST.get('empid')
        # empname=request.POST.get('empname')
        empid="123"
        empname="sudha"
        date=request.POST['select_date']
        print('------------------',empid)
        print('------------------',empname)
        print('------------------',date)
        data={
            'employeeid':empid,
            'employeename':empname,
            'start_date':date,
            "end_date":"2024-02-25",
             "request_type":"single_date"
        }
        flask_url="http://localhost:5000/get_status_update_data"
        response=requests.post(flask_url,json=data)
        if response.status_code==200:
            flask_response=response.json()
            status_update=flask_response['status_update']
            print(flask_response)
            return render(request,'user/status.html',{"status_update":status_update})
            
        else:
            print("error",response.status_code)
    else:
        print('Failed to fetch location details. Status Code:')
    return render(request,'status.html')

def get_Status_Data(request):
    if request.method=='POST':
        start_date=request.POST['start_date']
        end_date=request.POST['end_date']
        print("start-date end_date",start_date,end_date)
        data={
            "start_date":start_date,
            "end_date":end_date,
            "employeeid":"123",
            "request_type":"in_between_dates"
        }
        flask_url="http://localhost:5000/get_status_update_data"
        response=requests.post(flask_url,json=data)
        if response.status_code==200:
            response_date=response.json()
            print(response)
            total_status_data=response_date['request_data']
            print(total_status_data)
            return render(request,'user/status.html',{"total_data":total_status_data})
            print("data is going")
        else:
            print("data is not going",response.status_code)
    return render(request,'status.html')

def update_Status(request):
    pass

@csrf_exempt
def update_location(request):
    print("🔥 DJANGO update_location HIT 🔥")
    print("POST DATA:", request.POST)
    # return JsonResponse({"status": "ok"})
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        username = request.POST.get('username')
        email= request.POST.get ('email')
        buttonname=request.POST.get('buttonname')
        id = request.POST.get('userid')
        print("button name",request.POST.get('buttonname'))
        print(username,email,"userid-",id)
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"

        response = requests.get(url)
        print(response)
        if response.status_code == 200:
            print("Hit 200")
            data = response.json()
            print(data)
            if 'error' not in data:
                historic = data.get('locality') or data.get('city') or 'Unknown City'
                district = data.get('principalSubdivision') or 'Unknown State'

                print("📍 City:", historic)
                print("📍 State:", district)
                data={
                        'employee_id':id,
                        'employee_name':username,
                        'historic':historic,
                        'district':district,
                        'button_name':buttonname
                    }
                print("data that I am sending is ",data)
                flask_url="http://localhost:5000/clock_in"
                response=requests.post(flask_url,json=data)
                flask_response=response.json()
                print("clock and clockout response is",flask_response)
                print(flask_response)
                if flask_response['message']=='Clock-in successful':
                        response_data={
                            "message":"success",
                            "current_time":flask_response['current_time']
                        }
                        return JsonResponse(response_data)
                elif flask_response['message']=='Already clocked in today':
                        response_data={
                            "message":"failed",
                            "current_time":flask_response['current_time']
                        }
                        return JsonResponse(response_data)
                elif flask_response['message']=='No clock-in record found':
                        response_data={
                            "message":"failed",
                            "current_time":''
                        }
                        return JsonResponse(response_data)
                elif flask_response['message']=='Clock-out successful':
                    response_data={
                            "message":"success",
                            "current_time":'',
                            "working_hours": flask_response['working_hours']
                        }
                    return JsonResponse(response_data)
                elif flask_response['message']=="Clock-out already recorded":
                        response_data={
                            "message":"failed",
                            
                        }
                        return JsonResponse(response_data)
    #             if flask_response['status']=="success":
    #                 print("this is the response data",flask_response)
    #                 print("clock in success")
    #                 print(flask_response['current_time'])
    #                 input_date = datetime.strptime(flask_response['current_time'], "%a, %d %b %Y %H:%M:%S %Z")
                    
    #                 current_time = input_date.strftime("%H-%M-%S")
    #                 response_data={
    #                     "message":"success",
    #                     "current_time":current_time
    #                 }
    #                 print(response_data)
    #                 print("current time if:",current_time)
    #                 return JsonResponse(response_data)
    #             else:
    #                 message = flask_response.get('message', '')

    #                 # 👇 Case 1: Already clocked in
    #                 if "Already clocked in" in message:
    #                     return JsonResponse({
    #                         "message": "already_clocked_in",
    #                         "current_time": flask_response.get("current_time", "")
    #                     })

    #                 # 👇 Case 2: Actual clock out
    #                 if flask_response.get("status") == "clock_out_success":
    #                     return JsonResponse({
    #                         "message": "clock_out_success",
    #                         "current_time": flask_response.get("current_time", "")
    #                     })
    #                 try:
    #                     print("upto this executed................")
    #                     current_time_str = flask_response['current_time']
    #                     # current_time_str = datetime.strptime(current_time_str, "%H:%M:%S")
    #                     print("Clock In Time:", current_time_str)
    #                     # current_time_str = datetime.strptime(flask_response['current_time'], "%a, %d %b %Y %H:%M:%S %Z")
    #                     datetime_obj = datetime.strptime(current_time_str, "%a, %d %b %Y %H:%M:%S %Z")
    #                     avg_working_hrs = datetime_obj.strftime("%H:%M:%S")
    #                     # # print(Clock_In_Time)
    #                     # avg_working_hrs = current_time_str.strftime("%H:%M:%S")
    #                     # avg_working_hrs=current_time_str
    #                     print("...................................")
    #                     print("average working hours",avg_working_hrs)                     
    #                     response_data={
    #                         "message":"success",
    #                         "current_time":avg_working_hrs } 
    #                     # return JsonResponse(response_data)
    #                     print("clock in time in try block",avg_working_hrs)
    #                     return JsonResponse(response_data)
    #                 except Exception as e:
    #                     print("already clockin person pressing clock in again")
                        
    #                 #return render(request, 'sample.html', {"username":"varun"})
    #         else:
    #             print('Failed to fetch location details.')
    #     else:
    #         print('Failed to fetch location details. Status Code:', response.status_code)
    # response_data={
    #                     "message":"success",
    #                     "current_time":""
    #                 }   
    # return JsonResponse(response_data)



@login_required
def accept(request):

    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    user_id = session_user['user_id']

    data = {
        "employee_id": user_id,
        "request_type": "accept"
    }

    flask_url = "http://localhost:5000/accepted_leave_history"

    try:
        response = requests.post(flask_url, json=data)

        if response.status_code != 200:
            print("Flask error:", response.status_code)
            return render(request, 'user/accept.html', session_user)

        response_data = response.json()
        accepted_data = response_data.get('Employee_Leave_history', [])

    except Exception as e:
        print("Flask request failed:", e)
        return render(request, 'user/accept.html', session_user)

    # ✅ Safe Date Formatting
    def safe_format(date_string):
        try:
            input_date = datetime.strptime(
                date_string,
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            return input_date.strftime("%Y-%m-%d")
        except:
            return date_string

    for item in accepted_data:
        item['Start_date'] = safe_format(item.get('Start_date'))
        item['End_date'] = safe_format(item.get('End_date'))

    return render(
        request,
        'user/accept.html',
        {
            **session_user,
            "accepted_data": accepted_data
        }
    )

@login_required
def pending(request):

    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    user_id = session_user['user_id']

    flask_url = "http://localhost:5000/accepted_leave_history"

    data = {
        "employee_id": user_id,   # 🔐 from session only
        "request_type": "pending"
    }

    accepted_data = []

    try:
        response = requests.post(flask_url, json=data)

        if response.status_code != 200:
            print("Flask error:", response.status_code)
            return render(request, 'user/pending.html', session_user)

        response_data = response.json()
        accepted_data = response_data.get('Employee_Leave_history', [])

    except Exception as e:
        print("Flask request failed:", e)
        return render(request, 'user/pending.html', session_user)

    # ✅ Safe date formatting
    for item in accepted_data:

        # Start Date
        try:
            item['Start_date'] = date_convertion(item['Start_date'])
        except:
            pass

        # Applied On
        try:
            item['Applied_on'] = date_convertion(item['Applied_on'])
        except:
            pass

        # End Date
        try:
            if isinstance(item['End_date'], str):
                dt = datetime.strptime(
                    item['End_date'],
                    "%a, %d %b %Y %H:%M:%S %Z"
                )
                item['End_date'] = dt.strftime("%Y-%m-%d")
        except:
            pass

    return render(
        request,
        'user/pending.html',
        {
            **session_user,
            "accepted_data": accepted_data
        }
    )


@login_required
def reject(request):

    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    user_id = session_user['user_id']

    data = {
        "employee_id": user_id,
        "request_type": "reject"
    }

    flask_url = "http://localhost:5000/accepted_leave_history"

    try:
        response = requests.post(flask_url, json=data)

        if response.status_code != 200:
            print("Flask returned error:", response.status_code)
            return render(request, 'user/reject.html', session_user)

        response_data = response.json()

    except Exception as e:
        print("Flask request failed:", e)
        return render(request, 'user/reject.html', session_user)

    # Extract safely
    Rejected_data = response_data.get('Emp_Rejected_Info', [])

    for item in Rejected_data:
        try:
            item['Start_date'] = date_convertion(item.get('Start_date'))
            item['End_date'] = date_convertion(item.get('End_date'))
        except Exception as e:
            print("Date conversion error:", e)

    return render(
        request,
        'user/reject.html',
        {
            **session_user,
            "Rejected_data": Rejected_data
        }
    )
@login_required
def leave(request):
    # 🔑 Read user info from session
    session_user = get_session_user(request)

    return render(
        request,
        'leave.html',
        session_user
    )

# ─── Global date helper used by leave_status and others ───
def safe_date(val):
    """Convert any date string format to YYYY-MM-DD, return as-is if it fails."""
    if not val:
        return ''
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(val), fmt).strftime("%Y-%m-%d")
        except:
            continue
    return str(val)

@login_required
def leave_status(request):
    username = request.session.get('username')
    email = request.session.get('user_email')
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Fetch employee count + all names
    flask_url = "http://localhost:5000/get_employees_count"
    response = requests.post(flask_url, json={"request_type": "get_employess"})

    Employee_Count = None
    All_Names_Ids = []
    Employee_LeaveRequest_Info = []  # ✅ fixed variable name

    if response.status_code == 200:
        response_data = response.json()
        try:
            Employee_Count = response_data['Total_employees'][0]['COUNT(Employee_id)']
            All_Names_Ids = response_data['all_employee_name_id']
        except Exception as e:
            print("Error parsing employee count:", e)

    Employee_ID = None
    Employee_Name = None
    date_filter = None

    if request.method == 'POST':
        # ── Search by employee name/ID ──
        raw = request.POST.get('nameInput', '').strip()
        date_filter = request.POST.get('dateFilter', '').strip() or None

        # Parse "ID Name" format from autocomplete
        parts = raw.split(' ', 1)
        if len(parts) == 2 and parts[0].isdigit():
            Employee_ID = parts[0]
            Employee_Name = parts[1]
        else:
            Employee_Name = raw

        # Use the existing /get_leaverequest_data endpoint which accepts employee_id
        resp2 = requests.post(
            "http://localhost:5000/get_leaverequest_data",
            json={"employee_id": Employee_ID}
        )
        if resp2.status_code == 200:
            raw_leaves = resp2.json().get('Employee_Leave_request_data', [])
            # Always assign both casing variants so template never raises VariableDoesNotExist
            for lv in raw_leaves:
                _lt = lv.get('Leave_Type') or lv.get('Leave_type') or ''
                lv['Leave_Type'] = _lt
                lv['Leave_type'] = _lt
                _nd = lv.get('No_of_Days') or lv.get('No_of_days') or ''
                lv['No_of_Days'] = _nd
                lv['No_of_days'] = _nd
                if 'Status' not in lv:
                    lv['Status'] = 'Waiting'
            # Apply date filter client-side if provided
            if date_filter:
                raw_leaves = [
                    lv for lv in raw_leaves
                    if lv.get('Start_date', '') <= date_filter <= lv.get('End_date', '')
                ]
            Employee_LeaveRequest_Info = raw_leaves

    else:
        # ── GET: load ALL pending leave requests using existing endpoint ──
        # /get_employees_count already returns Leave_Request_Info (Status='Waiting')
        if response.status_code == 200:
            raw_all = response_data.get('Leave_Request_Info', [])
            for lv in raw_all:
                _lt = lv.get('Leave_Type') or lv.get('Leave_type') or ''
                lv['Leave_Type'] = _lt
                lv['Leave_type'] = _lt
                _nd = lv.get('No_of_Days') or lv.get('No_of_days') or ''
                lv['No_of_Days'] = _nd
                lv['No_of_days'] = _nd
                if 'Status' not in lv:
                    lv['Status'] = 'Waiting'
            Employee_LeaveRequest_Info = raw_all

    # Normalize dates
    for lv in Employee_LeaveRequest_Info:
        lv['Applied_on'] = safe_date(lv.get('Applied_on', ''))
        lv['Start_date'] = safe_date(lv.get('Start_date', ''))
        lv['End_date']   = safe_date(lv.get('End_date', ''))

    return render(request, 'Admin/leavestats.html', {
        "Employee_Count": Employee_Count,
        "All_Names_Ids": All_Names_Ids,
        "Employee_LeaveRequest_Info": Employee_LeaveRequest_Info,  # ✅ fixed name
        "Employee_ID": Employee_ID,
        "Employee_Name": Employee_Name,
        "date_filter": date_filter,
        "username": username,
        "email": email,
        "user_id": user_id,
        "user_type": user_type,
    })


@login_required
def leave_accept(request, request_id):
    session_user = get_session_user(request)
    if not session_user:
        return redirect('login')

    allowed_roles = ["employer", "manager", "team lead", "teamlead", "admin"]
    if session_user['user_type'].lower() not in allowed_roles:
        return HttpResponse("Unauthorized", status=403)

    flask_url = f"http://localhost:5000/accept/{request_id}/{session_user['username']}"
    try:
        response = requests.post(flask_url)
        if response.status_code == 200:
            print(f"✅ Leave {request_id} accepted")
    except Exception as e:
        print("Flask request failed:", e)

    return redirect('get_Employee_Leaves')   # ✅ redirect back to leave stats


@login_required
def leave_reject(request, request_id):
    session_user = get_session_user(request)
    if not session_user:
        return redirect('login')

    allowed_roles = ["employer", "manager", "team lead", "teamlead", "admin"]
    if session_user['user_type'].lower() not in allowed_roles:
        return HttpResponse("Unauthorized", status=403)

    flask_url = f"http://localhost:5000/reject/{request_id}/{session_user['username']}"
    try:
        response = requests.post(flask_url)
        if response.status_code == 200:
            print(f"❌ Leave {request_id} rejected")
    except Exception as e:
        print("Flask request failed:", e)

    return redirect('get_Employee_Leaves')
     

def date_convertion(i_date):
    # accepted_data[i]['Start_date']
    input_date = datetime.strptime(i_date , "%a, %d %b %Y %H:%M:%S %Z")
    start_date = input_date.strftime("%Y-%m-%d")
    return start_date
  




@login_required
def check(request):
    # 🔐 identity from session
    user = get_session_user(request)

    username = user['username']
    user_type = user['user_type']
    email = user['email']
    user_id = user['user_id']

    print(username, user_type, email, user_id)

    # ================= EMPLOYEE NAMES =================
    flask_url = "http://localhost:5000/send_all_employee"
    data = {
        "request": "all_Employee_Names",
        "employee_id": user_id,
        "username": username
    }

    response = requests.post(flask_url, json=data)
    Employee_Names = []

    if response.status_code == 200:
        response_data = response.json()
        print("this is the response", response_data)
        Employee_Names = response_data.get('Employee_names', [])

    # ── POST: Apply a new leave ──────────────────────────────
    apply_success = None
    apply_error   = None
    fromdate = to_date_disp = applied_on_disp = None

    if request.method == 'POST':
        from_Date  = request.POST.get('from_date', '').strip()
        to_Date    = request.POST.get('to_date', '').strip()
        Leave_Type = request.POST.get('leave_type', '').strip()
        Reason     = request.POST.get('reason', '').strip()

        try:
            d1 = datetime.strptime(from_Date, "%Y-%m-%d").date()
            d2 = datetime.strptime(to_Date,   "%Y-%m-%d").date()
            if d1 > d2:
                apply_error = "Start date cannot be after end date."
            else:
                flask_resp = requests.post(
                    "http://localhost:5000/leave_request_data",
                    json={
                        "from_date":     from_Date,
                        "to_date":       to_Date,
                        "leave_type":    Leave_Type,
                        "reason":        Reason,
                        "employee_name": username,
                        "id":            user_id,
                        "request_type":  "insert"
                    }
                )
                if flask_resp.status_code == 200:
                    rd = flask_resp.json()
                    # Flask returns dates in RFC format — parse safely
                    def _fmt(v):
                        if not v: return v
                        for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d"):
                            try: return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
                            except: continue
                        return v
                    fromdate       = _fmt(rd.get('From_date', from_Date))
                    to_date_disp   = _fmt(rd.get('To_date', to_Date))
                    applied_on_disp = rd.get('Applied_on', '')
                    apply_success  = True
                else:
                    apply_error = "Leave application failed. Please try again."
        except Exception as e:
            print("Apply leave error:", e)
            apply_error = "An error occurred. Please check the dates."

    # ── Fetch ALL leave records for this employee ──────────
    all_leave_response = requests.post(
        "http://localhost:5000/get_employee_all_leaves",
        json={"employee_id": user_id}
    )

    All_Leave_Info = []
    if all_leave_response.status_code == 200:
        raw_leaves = all_leave_response.json().get('all_leaves', [])
        for lv in raw_leaves:
            raw_status = lv.get('Status', 'Waiting')
            if raw_status == 'Waiting':
                lv['Status'] = 'Pending'
            elif raw_status == 'Accepted':
                lv['Status'] = 'Approved'
            for f in ('Applied_on', 'Start_date', 'End_date'):
                lv[f] = safe_date(lv.get(f, ''))
            lv['Leave_type'] = lv.get('Leave_Type') or lv.get('Leave_type') or ''
            lv['No_of_days'] = lv.get('No_of_Days') or lv.get('No_of_days') or ''
            All_Leave_Info.append(lv)

    return render(request, 'user/demo.html', {
        **user,
        'Employee_Names':   Employee_Names,
        'All_Leave_Info':   All_Leave_Info,
        'apply_success':    apply_success,
        'apply_error':      apply_error,
        'fromdate':         fromdate,
        'to_date':          to_date_disp,
        'applied_on':       applied_on_disp,
    })

@login_required
def leaveManagement(request):
    session_user = get_session_user(request)

    username = session_user['username']
    email = session_user['email']
    user_type = session_user['user_type']
    user_id = session_user['user_id']

    # 🔹 Get employee names + leave data
    data = {
        "request": "all_Employee_Names",
        "employee_id": user_id,
        "username": username
    }

    flask_url = "http://localhost:5000/send_all_employee"
    response = requests.post(flask_url, json=data)

    leaves_data = []
    if response.status_code == 200:
        response_data = response.json()
        print("this is the response", response_data)
        leaves_data = response_data.get('employee_leaves_data', [])

    # ================= POST (Apply Leave) =================
    if request.method == 'POST':
        from_Date = request.POST.get('from_date')
        to_Date = request.POST.get('to_date')
        Leave_Type = request.POST.get('leave_type')
        Reason = request.POST.get('reason')
        Selected_Persons = request.POST.getlist('addperson')

        print("leaves", Leave_Type, Reason, Selected_Persons)
        print(from_Date, to_Date)

        dateobject1 = datetime.strptime(from_Date, "%Y-%m-%d").date()
        dateobject2 = datetime.strptime(to_Date, "%Y-%m-%d").date()

        if dateobject1 > dateobject2:
            print("Invalid date range")

        else:
            data = {
                "from_date": from_Date,
                "to_date": to_Date,
                "leave_type": Leave_Type,
                "reason": Reason,
                "employee_name": username,
                "id": user_id,
                "request_type": "insert"
            }

            flask_url = "http://localhost:5000/leave_request_data"
            response = requests.post(flask_url, json=data)

            if response.status_code == 200:
                response_data = response.json()

                from_date1 = datetime.strptime(
                    response_data['From_date'],
                    "%a, %d %b %Y %H:%M:%S %Z"
                ).strftime("%Y-%m-%d")

                to_date1 = datetime.strptime(
                    response_data['To_date'],
                    "%a, %d %b %Y %H:%M:%S %Z"
                ).strftime("%Y-%m-%d")

                return render(
                    request,
                    'user/demo.html',
                    {
                        **session_user,
                        "fromdate": from_date1,
                        "to_date": to_date1,
                        "applied_on": response_data['Applied_on']
                    }
                )

    return render(
        request,
        'user/demo.html',
        {
            **session_user,
            "leaves_data": leaves_data
        }
    )


@login_required
def search(request):
    username = request.session.get('username')
    email = request.session.get('user_email')
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    flask_url = "http://localhost:5000/get_employees_count"
    data = {
        "request_type": "get_employess"
    }

    response = requests.post(flask_url, json=data)

    if response.status_code == 200:
        response_data = response.json()
        try:
            Employee_Count = response_data['Total_employees'][0]['COUNT(Employee_id)']
            All_Names_Ids = response_data['all_employee_name_id']
            Clock_Info = response_data['Clock_Info']

            return render(
                request,
                'Admin/search.html',
                {
                    "Employee_Count": Employee_Count,
                    "All_Names_Ids": All_Names_Ids,
                    "Clock_Info": Clock_Info,
                    "username": username,
                    "email": email,
                    "user_id": user_id,
                    "user_type": user_type,
                }
            )
        except Exception as e:
            print("Error in search view:", e)

    return render(
        request,
        'Admin/search.html',
        {
            "username": username,
            "email": email,
            "user_id": user_id,
            "user_type": user_type,
        }
    )


def opening(request,username,user_type,email,user_id):
    flask_url="http://localhost:5000/get_employees_count"
    data={
        "request_type":"get_employess"
    }
    response=requests.post(flask_url,json=data)
    response_data=response.json()
    if response.status_code==200:
        try: 
           Employee_Count=response_data['Total_employees'][0]['COUNT(Employee_id)']
           All_Names_Ids=response_data['all_employee_name_id']
           print(All_Names_Ids)
           print("data is going")
           return render(request,'Admin/opening.html',{"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,
                                                "username":username,'email':email,'user_id':user_id,'user_type':user_type,})
        except:
            print("error is coming at admin page")
    else:
        print("data is not going",response.status_code)
    return render(request,'Admin/opening.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type,})



@login_required
def get_Employee_Attendance(request):

    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    if session_user['user_type'].lower() != "employer":
        return HttpResponse("Unauthorized", status=403)

    if request.method == "POST":

        name_input  = request.POST.get("nameInput", "").strip()
        date_filter = request.POST.get("dateFilter", "").strip()   # NEW

        if not name_input:
            return redirect("get_Employee_Attendance")

        parts = name_input.split()
        selected_emp_id   = parts[0] if len(parts) > 0 else ""
        selected_emp_name = parts[1] if len(parts) > 1 else ""

        flask_url = "http://localhost:5000/get_employee_attendance"

        try:
            payload = {"employee_id": selected_emp_id}
            if date_filter:                          # send date only if provided
                payload["date_filter"] = date_filter

            response = requests.post(flask_url, json=payload)

            if response.status_code != 200:
                return render(request, "Admin/search.html", session_user)

            response_data = response.json()

        except Exception as e:
            print("Flask request failed:", e)
            return render(request, "Admin/search.html", session_user)

        try:
            Employee_Count = int(
                response_data['Total_employees'][0]['COUNT(Employee_id)']
            )
            All_Names_Ids         = response_data['all_employee_name_id']
            Employee_Attendance_Info = response_data.get('employee_clock_info', [])

            # client-side date filter fallback (if Flask doesn't filter)
            if date_filter and Employee_Attendance_Info:
                Employee_Attendance_Info = [
                    r for r in Employee_Attendance_Info
                    if str(r.get('Date', ''))[:10] == date_filter
                ]

            if Employee_Attendance_Info:
                Employee_Name = Employee_Attendance_Info[0]['employee_name']
                Employee_ID   = Employee_Attendance_Info[0]['Employee_id']
            else:
                Employee_Name = selected_emp_name
                Employee_ID   = selected_emp_id

            return render(
                request,
                "Admin/search.html",
                {
                    **session_user,
                    "Employee_Attendance_Info": Employee_Attendance_Info,
                    "Employee_ID":    Employee_ID,
                    "Employee_Name":  Employee_Name,
                    "Employee_Count": Employee_Count,
                    "All_Names_Ids":  All_Names_Ids,
                    "date_filter":    date_filter,   # pass back so form retains value
                }
            )

        except Exception as e:
            print("Error parsing attendance data:", e)

    return render(request, "Admin/search.html", session_user)


@login_required
def get_Employee_Leaves(request):

    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    if session_user['user_type'].lower() != "employer":
        return HttpResponse("Unauthorized", status=403)

    # ── Always fetch employee count + names + ALL pending leaves on GET ──
    base_response = requests.post(
        "http://localhost:5000/get_employees_count",
        json={"request_type": "get_employess"}
    )

    Employee_Count    = None
    All_Names_Ids     = []
    Employee_ID       = None
    Employee_Name     = None
    date_filter       = None
    Employee_LeaveRequest_Info = []

    if base_response.status_code == 200:
        base_data = base_response.json()
        try:
            Employee_Count = int(base_data['Total_employees'][0]['COUNT(Employee_id)'])
            All_Names_Ids  = base_data['all_employee_name_id']
        except Exception as e:
            print("Error parsing base data:", e)

    if request.method == "POST":
        name_input  = request.POST.get("nameInput", "").strip()
        date_filter = request.POST.get("dateFilter", "").strip() or None

        if not name_input:
            # No name typed → show all pending
            if base_response.status_code == 200:
                Employee_LeaveRequest_Info = base_data.get('Leave_Request_Info', [])
        else:
            parts = name_input.split()
            Employee_ID   = parts[0] if len(parts) > 0 else ""
            Employee_Name = parts[1] if len(parts) > 1 else ""

            resp2 = requests.post(
                "http://localhost:5000/get_leaverequest_data",
                json={"employee_id": Employee_ID}
            )

            if resp2.status_code == 200:
                Employee_LeaveRequest_Info = resp2.json().get('Employee_Leave_request_data', [])

            # Client-side date filter
            if date_filter and Employee_LeaveRequest_Info:
                Employee_LeaveRequest_Info = [
                    r for r in Employee_LeaveRequest_Info
                    if r.get('Start_date', '')[:10] <= date_filter <= r.get('End_date', '')[:10]
                ]

    else:
        # GET → show all pending leaves from get_employees_count
        if base_response.status_code == 200:
            Employee_LeaveRequest_Info = base_data.get('Leave_Request_Info', [])

    # Normalize dates and field names for template
    for lv in Employee_LeaveRequest_Info:
        lv['Applied_on'] = safe_date(lv.get('Applied_on', ''))
        lv['Start_date'] = safe_date(lv.get('Start_date', ''))
        lv['End_date']   = safe_date(lv.get('End_date', ''))
        # Always assign BOTH casing variants so Django template never raises VariableDoesNotExist
        # DB returns Leave_Type (capital T); template variable is Leave_type (lowercase t)
        _lt = lv.get('Leave_Type') or lv.get('Leave_type') or ''
        lv['Leave_Type'] = _lt
        lv['Leave_type'] = _lt
        _nd = lv.get('No_of_Days') or lv.get('No_of_days') or ''
        lv['No_of_Days'] = _nd
        lv['No_of_days'] = _nd
        if 'Status' not in lv:
            lv['Status'] = 'Waiting'

    return render(
        request,
        "Admin/leavestats.html",
        {
            **session_user,
            "Employee_LeaveRequest_Info": Employee_LeaveRequest_Info,
            "Employee_ID":    Employee_ID,
            "Employee_Name":  Employee_Name,
            "Employee_Count": Employee_Count,
            "All_Names_Ids":  All_Names_Ids,
            "date_filter":    date_filter,
        }
    )

# safe_date is defined globally above leave_status — no duplicate needed here



@login_required
def org(request):
    user_type = request.session.get('user_type')
    print(user_type)
    #no access for employee
    user_type=user_type.lower()
    if user_type == "employee":
            return redirect('home') 

    #  READ FROM SESSION (NOT URL)
    username = request.session.get('username')
    email = request.session.get('user_email')
    
    user_id = request.session.get('user_id')

    data = {
        "request": "all_employees"
    }

    flask_url = "http://localhost:5000/get_employees_count"
    response = requests.post(flask_url, json=data)

    All_Employee_Details = []

    if response.status_code == 200:
        response_data = response.json()
        print("response data from org is", response_data)

        All_Employee_Details = response_data.get('all_employee_name_id', [])

    else:
        print("some error coming in org method", response.status_code)

    org_structure = defaultdict(lambda: defaultdict(list))

    for emp in All_Employee_Details:

        manager = emp.get("Manager_name") or "Np Manager"
        team_lead = emp.get("Team_lead") or "No Team Lead"

        org_structure[manager][team_lead].append(emp)

    # convert defaultdict → normal dict
    
    org_structure = {manager: dict(teams) for manager, teams in org_structure.items()}


    return render(
        request,
        'Admin/org.html',
        {
            "username": username,
            "email": email,
            "user_id": user_id,
            "user_type": user_type,
            "org_structure": org_structure
        }
    )

@login_required
def update(request, Employee_id):
    user = get_session_user(request)

    data = {
        "Employee_id": Employee_id
    }

    flask_url = "http://localhost:5000/employee_details"
    response = requests.post(flask_url, json=data)

    Complete_Employee_Details = {}

    if response.status_code == 200:
        response_data = response.json()
        print("response data from update() is", response_data)

        try:
            Complete_Employee_Details = response_data['employee_complete_info']

            # Normalize date
            input_date = datetime.strptime(
                Complete_Employee_Details['Date'],
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            Complete_Employee_Details['Date'] = input_date.strftime("%Y-%m-%d")

        except Exception as e:
            print("Error in update():", e)

    return render(
        request,
        'Admin/update.html',
        {
            **user,
            "Complete_Employee_Details": Complete_Employee_Details
        }
    )
@login_required
def festival_data(request):
    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')
    
    username = session_user['username']
    email = session_user['email']
    user_type = session_user['user_type']
    user_id = session_user['user_id']
    user_type=user_type.lower()
    if user_type == "employee":
        return redirect('Fest_Info')
    
    if request.method == 'POST':
        date = request.POST.get('festival_date')
        name = request.POST.get('festival_name')

        data = {
            "date": date,
            "festival_name": name
        }

        flask_url = "http://localhost:5000/holiday"
        response = requests.post(flask_url, json=data)

        if response.status_code == 200:
            response_data = response.json()
            print("response data from festival is", response_data)

    return render(
        request,
        'Admin/Admin_fest_info.html',
        session_user
    )


@login_required
def Work_From_Home_accept(request, Request_id):

    # 🔑 Get user from session
    username = request.session.get('username')
    email = request.session.get('user_email')
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    print("WFH ACCEPT → Request ID:", Request_id)
    print("Action by:", username)

    flask_url = f"http://localhost:5000/WFH_accept/{Request_id}/{username}"
    response = requests.post(flask_url)

    if response.status_code != 200:
        return HttpResponse("Error processing WFH request")

    response_data = response.json()

    Employee_Count = response_data['Total_employees'][0]['COUNT(Employee_id)']
    All_Names_Ids = response_data['all_employee_name_id']

    try:
        Work_From_Home_Info = response_data['Work_From_Home_Info']

        for item in Work_From_Home_Info:
            item['Applied_on'] = datetime.strptime(
                item['Applied_on'], "%a, %d %b %Y %H:%M:%S %Z"
            ).strftime("%Y-%m-%d")

            item['Start_Date'] = datetime.strptime(
                item['Start_Date'], "%a, %d %b %Y %H:%M:%S %Z"
            ).strftime("%Y-%m-%d")

            item['End_Date'] = datetime.strptime(
                item['End_Date'], "%a, %d %b %Y %H:%M:%S %Z"
            ).strftime("%Y-%m-%d")

    except Exception as e:
        print("WFH parsing error:", e)
        Work_From_Home_Info = []

    return render(
        request,
        'Admin/acceptWFH.html',
        {
            "Employee_Count": Employee_Count,
            "All_Names_Ids": All_Names_Ids,
            "Work_From_Home_Info": Work_From_Home_Info,
            "username": username,
            "email": email,
            "user_id": user_id,
            "user_type": user_type,
        }
    )
   



def Work_From_Home_Reject(request,Request_id,user_name,user_type,email,user_id):
    userid=Request_id
    username=user_name
    print("this is for reject",Request_id,user_name)
    print("After")
    flask_url=f"http://localhost:5000/WFH_Reject/{userid}/{username}"
    response = requests.post(flask_url)
    print(response)
    if response.status_code==200:
        response_data=response.json()
        Employee_Count=response_data['Total_employees'][0]['COUNT(Employee_id)']
        All_Names_Ids=response_data['all_employee_name_id']
           
        try:
           
           Work_From_Home_Info=response_data['Work_From_Home_Info']
           print(All_Names_Ids)
           print("work from home information.....",Work_From_Home_Info)
           for i in range(len(Work_From_Home_Info)):
               input_date = datetime.strptime(Work_From_Home_Info[i]['Applied_on'], "%a, %d %b %Y %H:%M:%S %Z")
               Applied_on = input_date.strftime("%Y-%m-%d")
               Work_From_Home_Info[i]['Applied_on'] = Applied_on
               input_date2 = datetime.strptime(Work_From_Home_Info[i]['Start_Date'], "%a, %d %b %Y %H:%M:%S %Z")
               Start_Date = input_date2.strftime("%Y-%m-%d")
               Work_From_Home_Info[i]['Start_Date'] = Start_Date
               input_date3 = datetime.strptime(Work_From_Home_Info[i]['End_Date'], "%a, %d %b %Y %H:%M:%S %Z")
               End_Date = input_date3.strftime("%Y-%m-%d")
               Work_From_Home_Info[i]['End_Date'] = End_Date       
           print("data is going")
           print("rejected the leave..................")
           return render(request,'Admin/acceptWFH.html',{"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,"Work_From_Home_Info":Work_From_Home_Info,
                                                "username":username,'email':email,'user_id':user_id,'user_type':user_type,})
        except Exception as e:
             Work_From_Home_Info=""
             print("this is except",e)
             return render(request,'Admin/acceptWFH.html',{"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,"Work_From_Home_Info":Work_From_Home_Info,
                                                "username":username,'email':email,'user_id':user_id,'user_type':user_type,})
        # print(data_requested)
    else:
        print(response.status_code)
        return HttpResponse("prindingp")



def Work_From_Home_Action(request,Request_id,username,user_type,email,user_id,action):
    userid=Request_id
    username=username
    Action_Status= action
    print("this is for accept/reject",Request_id,username)
    print("After")
    print("status action is..........................",Action_Status)
    data={
        "Action_Status":Action_Status,
        "request_id":userid
    }
    flask_url="http://localhost:5000/update_work_from_home"
    response=requests.post(flask_url,json=data)
    print(response)
    if response.status_code==200:
        response_data=response.json()
        Employee_Count=response_data['Total_employees'][0]['COUNT(Employee_id)']
        All_Names_Ids=response_data['all_employee_name_id']     
        try:
           
           Work_From_Home_Info=response_data['Work_From_Home_Info']
           print(All_Names_Ids)
           print("work from home information.....",Work_From_Home_Info)
           for i in range(len(Work_From_Home_Info)):
               input_date = datetime.strptime(Work_From_Home_Info[i]['Applied_on'], "%a, %d %b %Y %H:%M:%S %Z")
               Applied_on = input_date.strftime("%Y-%m-%d")
               Work_From_Home_Info[i]['Applied_on'] = Applied_on
               input_date2 = datetime.strptime(Work_From_Home_Info[i]['Start_Date'], "%a, %d %b %Y %H:%M:%S %Z")
               Start_Date = input_date2.strftime("%Y-%m-%d")
               Work_From_Home_Info[i]['Start_Date'] = Start_Date
               input_date3 = datetime.strptime(Work_From_Home_Info[i]['End_Date'], "%a, %d %b %Y %H:%M:%S %Z")
               End_Date = input_date3.strftime("%Y-%m-%d")
               Work_From_Home_Info[i]['End_Date'] = End_Date           
           print("data is going")
           print("accepted the leave..................")
           return render(request,'Admin/acceptWFH.html',{"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,"Work_From_Home_Info":Work_From_Home_Info,
                                                "username":username,'email':email,'user_id':user_id,'user_type':user_type,})
        except Exception as e:
             Work_From_Home_Info=""
             print("this is except",e)
             return render(request,'Admin/acceptWFH.html',{"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,"Work_From_Home_Info":Work_From_Home_Info,
                                                "username":username,'email':email,'user_id':user_id,'user_type':user_type,})
        # print(data_requested)
    else:
        print(response.status_code)
        return HttpResponse("prindingp")

@login_required
def submit_employee_data(request, Request_type):
    """
    Handles insert/update employee data using SESSION
    """

    # 🔐 GET USER FROM SESSION (single source of truth)
    user = get_session_user(request)

    if not user['user_id']:
        return redirect('login')

    # ================= GET ALL EMPLOYEES =================
    All_Employee_Details = []
    flask_url = "http://localhost:5000/get_employees_count"

    response = requests.post(
        flask_url,
        json={"request": "all_employees"}
    )

    if response.status_code == 200:
        response_data = response.json()
        All_Employee_Details = response_data.get('all_employee_name_id', [])
    else:
        print("❌ Error fetching employee list")

    # ================= HANDLE POST =================
    if request.method == 'POST':
        data = request.POST.dict()

        # 🔑 IMPORTANT: inject request_type from URL
        data['request_type'] = Request_type

        print("📤 Sending to Flask:", data)

        flask_url = "http://localhost:5000/employee_complete_details"
        response = requests.post(flask_url, json=data)

        if response.status_code == 200:
            print("✅ Flask response:", response.json())
        else:
            print("❌ Flask error:", response.status_code)

    # ================= FINAL RENDER =================
    return render(
        request,
        'Admin/org.html',
        {
            **user,  # expands username, email, user_id, user_type
            "All_Employee_Details": All_Employee_Details
        }
    )
#getting fest and employee_leave balance info.............
@login_required
def Fest_Info(request):

    session_user = get_session_user(request)
    user_id = session_user['user_id']

    flask_url = 'http://localhost:5000/fest_info'

    try:
        response = requests.post(flask_url, json={
            'employee_id': user_id
        })

        if response.status_code != 200:
            print("Flask error:", response.status_code)
            return render(request, 'user/fest_info.html', session_user)

        flask_data = response.json()
        print("Flask data:", flask_data)

    except Exception as e:
        print("Flask request failed:", e)
        return render(request, 'user/fest_info.html', session_user)

    # -----------------------------
    # Extract Data Safely
    # -----------------------------

    Festival_Info = flask_data.get('Fest_Info', [])
    Leave_Balance_Info = flask_data.get('Leave_Balance_Info', [])
    Announcement_info = flask_data.get('announcement_info', [])
    date_of_births = flask_data.get('date_of_births', [])
    holiday_info = flask_data.get('holiday_info', [])
    leaves_info = flask_data.get('leaves_info', [])

    # -----------------------------
    # Format Dates Safely
    # -----------------------------

    def safe_format(date_string):
        try:
            input_date = datetime.strptime(
                date_string,
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            return input_date.strftime("%Y-%m-%d")
        except:
            return date_string

    for item in Festival_Info:
        item['Holiday_date'] = safe_format(item.get('Holiday_date'))

    for item in leaves_info:
        item['Start_date'] = safe_format(item.get('Start_date'))
        item['End_date'] = safe_format(item.get('End_date'))

    for item in Announcement_info:
        item['Announcement_date'] = safe_format(
            item.get('Announcement_date')
        )

    # -----------------------------
    # Final Render
    # -----------------------------

    return render(
        request,
        'user/fest_info.html',
        {
            **session_user,
            'flask_data': Festival_Info,
            'balance_info': Leave_Balance_Info,
            'announcement_info': Announcement_info,
            'date_of_births': date_of_births,
            'holiday_info': holiday_info,
            'leaves_info': leaves_info
        }
    )


#getting status update data based on request type(last month ,lasth_week ,last_day).............
def Status_Info(request):
    flask_url = 'http://localhost:5000/admin_get_status'
    data = {
        'Request_Type':'Last_day'
    }  
    #sending request to flask_url........
    response = requests.post(flask_url,json=data)
    if response.status_code == 200:
        #getting data from falsk...........
        data = response.json()
        print("the flask_data is....",data)
        print("above data ia from flask")
        try:
         Status_info=data['Status_Info']
         #sending status update data to html page for displaying..... 
         return render(request,'status.html',{'flask_data':Status_info})
        except Exception as e:
            print("error occuring in Fest INfo function. may be festival data not found")        
            return render(request,'status.html',{'flask_data':data})

        # return JsonResponse(data)       
    else:
        print("error is",response.status_code)
        return JsonResponse({'status': 'error', 'message': 'Failed to send request to Flask app'})





#getting fest and employee_leave balance info.............
def Admin_Fest_Info(request,username,user_type,email,user_id):
    flask_url = 'http://localhost:5000/fest_info'
    data = {
        'employee_id':'123'
    }  
    #sending request to flask_url........
    # try:
    response = requests.post(flask_url,json=data)
    # except Exception as e:
    #     print('exception ',e)
    if response.status_code == 200:
        #getting data from falsk...........
        data = response.json()
        print("the flask_data is....",data)
        try:
         Festival_Info=data['Fest_Info']
        #  Leave_Balance_Info=data['Leave_Balance_Info']
        #  Holiday_Date=Festival_Info[0]['Holiday_date']
        #  current_Date_Formatted= datetime.strptime(Holiday_Date, '%Y-%m-%d')
        #  print("currentlu",current_Date_Formatted)
         for i in range(len(Festival_Info)):
            input_date = datetime.strptime(Festival_Info[i]['Holiday_date'] , "%a, %d %b %Y %H:%M:%S %Z")
            Start_date = input_date.strftime("%Y-%m-%d")
            Festival_Info[i]['Holiday_date']=Start_date
         print("festival data is",Festival_Info)
        #  print("holiday date is..",Holiday_Date)
        #  print("holiday date is..",current_Date_Formatted)
         #sending fest and leave balance data to html page for displaying..... 
         return render(request,'user/fest_info.html',{'flask_data':Festival_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
        except Exception as e:
            print("error occuring in Fest INfo function. may be festival data not found")
            Festival_Info=""
        return render(request,'user/fest_info.html',{'flask_data':Festival_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
        # return JsonResponse(data)
    else:
        print("error is",response.status_code)
        return JsonResponse({'status': 'error', 'message': 'Failed to send request to Flask app'})


#................................................Attendance Info............................................................    
#getting Attendance data based on request type(last month ,lasth_week ,last_day).............
def Attendance_Info(request,username,user_type,email,user_id,Request_type,Emp_id):
    print(Request_type,Emp_id)
    Flask_Url = 'http://localhost:5000/admin_get_attendance'
    Data = {
        'Request_Type':Request_type,
        "Emp_id":Emp_id
    }  
    #sending request to flask_url........
    Response = requests.post(Flask_Url,json=Data)
    
    if Response.status_code == 200:
        #getting data from falsk...........
        Data = Response.json()
        print("the flask_data is....",Data)
        try:
             Attendance_Info=Data['Clock_Info']
             Employee_Name=Data['Clock_Info'][0]['employee_name']
        except:
            print("getting error in Attendance info may be data not found")
            Attendance_Info=""
            Employee_Name=""
        Employee_Count=Data['Employee_Count'][0]['COUNT(Employee_id)']
        print("employee",Employee_Count)
        All_Names_Ids=Data['All_Names_Ids']
        try:
         Attendance_Info=Data['Clock_Info']
         Employee_Count=Data['Employee_Count'][0]['COUNT(Employee_id)']
         print("employee",Employee_Count)
         All_Names_Ids=Data['All_Names_Ids']
         Employee_Name=Data['Clock_Info'][0]['employee_name']

         #sending Attendance  data to html page for displaying..... 
         return render(request,'Admin/search.html',{"Employee_Attendance_Info":Attendance_Info,"Employee_ID":Emp_id,
                                                     "username":username,'email':email,'user_id':user_id,'user_type':user_type,"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,"Employee_Name":Employee_Name})  
        except Exception as e:
            Attendance_Info=""
            print("error occuring in Fest INfo function. may be festival data not found")        
            return render(request,'Admin/search.html',{"Employee_Attendance_Info":Attendance_Info,"Employee_ID":Emp_id,
                                                     "username":username,'email':email,'user_id':user_id,'user_type':user_type,"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,"Employee_Name":Employee_Name})       
    else:
        print("error is",Response.status_code)
        return JsonResponse({'status': 'error', 'message': 'Failed to send request to Flask app'})

@login_required
def status(request):
    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    username = session_user['username']
    email = session_user['email']
    user_type = session_user['user_type']
    user_id = session_user['user_id']

    if request.method == 'POST':
        date = request.POST.get('date')
        completed_tasks = request.POST.get('completed')
        issues = request.POST.get('issues') or 'No Issues'
        feature_targets = request.POST.get('targets')
        status_update = request.POST.get('status')

        data = {
            'employeeid': user_id,
            'employeename': username,
            'email': email,
            'completed': completed_tasks,
            'issues': issues,
            'upcoming': feature_targets,
            'statusUpdate': status_update,
            'date': date
        }

        response = requests.post(
            "http://localhost:5000/status_update_data",
            json=data
        )

    return render(request, 'user/status.html', session_user)

# def status(request):
#     print("this is status function of django")
#     if request.method=='POST':
#         completed_tasks=request.POST.get('completed')
        
#         issues=request.POST.get('issues')
#         print(completed_tasks,issues)
#         feature_targets=request.POST['targets']
#         status_update=request.POST['status']
#         empid="123"
#         empname="sudha"
#         # empid=request.POST.get('empid')
#         # empname=request.POST.get('empname')
#         print('------------------',completed_tasks)
#         print('------------------',issues)
#         print('------------------',feature_targets,status_update)
       

#         if issues is None:
#             issues='No Issues'
   
#         data={
#             'employeeid':empid,
#             'employeename':empname,
#             'email':request.session['email'],
#             'completed':completed_tasks,
#             'issues':issues,
#             'upcoming':feature_targets,
#             'statusUpdate':status_update
#         }
#         flask_url="http://localhost:5000/status_update_data"
#         response=requests.post(flask_url,json=data)
#         flask_response=response.json()
#         print(flask_response)
#     else:
#         print('Failed to fetch location details. Status Code:')
#     return render(request,'user/status.html')

@login_required
def status_update(request):

    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    username  = session_user['username']
    email     = session_user['email']
    user_id   = session_user['user_id']
    user_type = session_user['user_type']

    Employee_Status_updates = []

    if request.method == "POST":

        start_date = request.POST.get('startdate')
        end_date   = request.POST.get('enddate')

        flask_url = "http://localhost:5000/get_status_update_data"

        data = {
            "employeeid": user_id,   # 🔐 from session only
            "start_date": start_date,
            "end_date": end_date,
            "request_type": "in_between_dates"
        }

        try:
            response = requests.post(flask_url, json=data)

            if response.status_code != 200:
                print("Flask error:", response.status_code)
                return render(request, 'user/status.html', session_user)

            flask_response = response.json()

        except Exception as e:
            print("Flask request failed:", e)
            return render(request, 'user/status.html', session_user)

        Employee_Status_updates = flask_response.get("request_data", [])

        # ✅ Safe date formatting
        for item in Employee_Status_updates:
            try:
                if isinstance(item['Date'], str):
                    dt = datetime.strptime(
                        item['Date'],
                        "%a, %d %b %Y %H:%M:%S %Z"
                    )
                    item['Date'] = dt.strftime("%Y-%m-%d")
            except:
                pass

        return render(
            request,
            'user/status.html',
            {
                **session_user,
                "Employee_Status_updates": Employee_Status_updates,
                "start_date": start_date,
                "end_date": end_date
            }
        )

    # 🔵 GET request (first load)
    return render(
        request,
        'user/status.html',
        session_user
    )


#getting fest and employee_leave balance info.............
def Admin_Holiday_Info(request,username,user_type,email,user_id):
    flask_url = 'http://localhost:5000/Admin_fest_info'
    data = {
        'employee_id':user_id
    }  
    print("user_id is",user_id)
    #sending request to flask_url........
    # try:
    response = requests.post(flask_url,json=data)
    #     print('festival ersult',response)   
    # except Exception as e:
    #     print('exception ',e)
    if response.status_code == 200:
        #getting data from falsk...........
        data = response.json()
        print("the flask_data is....",data)
        try:
            Festival_Info=data['Fest_Info']
            Announcement_info=data['announcement_info']
            date_of_births=data['date_of_births']
            holiday_info=data['holiday_info']
            leaves_info=data['leaves_info']
            print("Leaves_info",leaves_info)

            for i in range(len(Festival_Info)):
                input_date = datetime.strptime(Festival_Info[i]['Holiday_date'] , "%a, %d %b %Y %H:%M:%S %Z")
                Start_date = input_date.strftime("%Y-%m-%d")
                Festival_Info[i]['Holiday_date']=Start_date
            print("festival data is",Festival_Info)
            print("........................................................")
            for i in range(len(leaves_info)):
               input_date = datetime.strptime(leaves_info[i]['End_date'], "%a, %d %b %Y %H:%M:%S %Z")
               End_date = input_date.strftime("%Y-%m-%d")
               leaves_info[i]['End_date'] = End_date
               input_date2 = datetime.strptime(leaves_info[i]['Start_date'], "%a, %d %b %Y %H:%M:%S %Z")
               Start_date = input_date2.strftime("%Y-%m-%d")
               leaves_info[i]['Start_date'] = Start_date
            print("............................................")
            print("leaves Info.......",leaves_info)
            print("....announcement",Announcement_info)
            for i in range(len(Announcement_info)):
               input_date = datetime.strptime(Announcement_info[i]['Announcement_date'], "%a, %d %b %Y %H:%M:%S %Z")
               End_date = input_date.strftime("%Y-%m-%d")
               Announcement_info[i]['Announcement_date'] = End_date
            
            for i in range(len(holiday_info)):
               input_date = datetime.strptime(holiday_info[i]['Holiday_date'], "%a, %d %b %Y %H:%M:%S %Z")
               Holiday_date = input_date.strftime("%Y-%m-%d")
               holiday_info[i]['Holiday_date'] = Holiday_date
            print("............................................")
            print("holiday Info.......",holiday_info)


            return render(request,'Admin/Admin_fest_info.html',{'flask_data':Festival_Info,"announcement_info":Announcement_info,"date_of_births":date_of_births,"holiday_info":holiday_info,"leaves_info":leaves_info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
        except Exception as e:
            print("error occuring in Fest INfo function. may be festival data not found")
            Festival_Info=""
        return render(request,'Admin/Admin_fest_info.html',{'flask_data':Festival_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
        # return JsonResponse(data)
    else:
        print("error is",response.status_code)
        return JsonResponse({'status': 'error', 'message': 'Failed to send request to Flask app'})






@login_required
def Partial_Leave(request):
    print(" Partial Leave Function Called")

    user = get_session_user(request)

    if request.method == "POST":

        select_time = request.POST.get("Select_Time_of_Day")
        reason = request.POST.get("reason")

        print("Selected:", select_time, "Reason:", reason)

        from_date = datetime.now().strftime('%Y-%m-%d')
        to_date = from_date

        data = {
            "from_date": from_date,
            "to_date": to_date,
            "leave_type": select_time,
            "reason": reason,
            "employee_name": user["username"],
            "id": user["user_id"],
            "request_type": "Partial"
        }

        flask_url = "http://localhost:5000/leave_request_data"
        response = requests.post(flask_url, json=data)

        if response.status_code == 200:
            response_data = response.json()
            print("Flask Response:", response_data)

            return render(
                request,
                "user/clock.html",
                {
                    **user,
                    "message": response_data.get("message", "Partial leave applied")
                }
            )

    # Default fallback
    return render(request, "user/clock.html", user)


@login_required
@login_required
def work_from_home(request):

    print("Work From Home view called")
    session_user = get_session_user(request)

    # ==================== POST → Submit new WFH request ====================
    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date   = request.POST.get('to_date')
        reason    = request.POST.get('reason')

        print("Received:", from_date, to_date, reason)

        try:
            start_date = datetime.strptime(from_date, '%Y-%m-%d')
            end_date   = datetime.strptime(to_date,   '%Y-%m-%d')

            data = {
                'from_date':     start_date.strftime('%Y-%m-%d'),
                'to_date':       end_date.strftime('%Y-%m-%d'),
                'reason':        reason,
                'employee_name': session_user['username'],
                'id':            session_user['user_id'],
                'request_type':  'insert'
            }

            flask_url = "http://localhost:5000/work_from_home"
            response  = requests.post(flask_url, json=data)

            if response.status_code == 200:
                print("WFH submitted successfully")
            else:
                print("Flask API failed:", response.status_code)

        except Exception as e:
            print("Error submitting WFH:", e)

        # ✅ Always redirect back to WFH page after submit (shows updated status)
        return redirect('work_from_home')

    # ==================== GET → Fetch employee's own WFH requests ====================
    wfh_info = []
    try:
        flask_url = "http://localhost:5000/get_employee_WFH_Info"
        response  = requests.post(flask_url, json={
            "employee_id": session_user['user_id']
        })

        if response.status_code == 200:
            response_data = response.json()
            wfh_info = response_data.get('employee_Emp_WHF_Info', [])

            # Format dates safely
            for item in wfh_info:
                for field in ['Applied_on', 'Start_Date', 'End_Date']:
                    try:
                        item[field] = datetime.strptime(
                            item[field], "%a, %d %b %Y %H:%M:%S %Z"
                        ).strftime("%Y-%m-%d")
                    except:
                        pass
        else:
            print("Flask WFH fetch failed:", response.status_code)

    except Exception as e:
        print("Error fetching WFH status:", e)

    return render(request, 'user/work_from_home.html', {
        **session_user,
        'wfh_info': wfh_info   # ✅ employee sees their WFH requests + status
    })


@login_required
def Work_from_home_accept(request):

    # 🔐 GET USER FROM SESSION
    username = request.session.get('username')
    email = request.session.get('user_email')
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    flask_url = "http://localhost:5000/get_employees_count"
    data = {
        "request_type": "get_employess"
    }

    response = requests.post(flask_url, json=data)

    if response.status_code == 200:
        response_data = response.json()
        try:
            Employee_Count = response_data['Total_employees'][0]['COUNT(Employee_id)']
            All_Names_Ids = response_data['all_employee_name_id']
            Work_From_Home_Info = response_data['Work_From_Home_Info']

            # 📅 Date formatting
            for item in Work_From_Home_Info:
                item['Applied_on'] = datetime.strptime(
                    item['Applied_on'], "%a, %d %b %Y %H:%M:%S %Z"
                ).strftime("%Y-%m-%d")

                item['Start_Date'] = datetime.strptime(
                    item['Start_Date'], "%a, %d %b %Y %H:%M:%S %Z"
                ).strftime("%Y-%m-%d")

                item['End_Date'] = datetime.strptime(
                    item['End_Date'], "%a, %d %b %Y %H:%M:%S %Z"
                ).strftime("%Y-%m-%d")

            return render(
                request,
                'Admin/acceptWFH.html',
                {
                    "Employee_Count": Employee_Count,
                    "All_Names_Ids": All_Names_Ids,
                    "Work_From_Home_Info": Work_From_Home_Info,
                    "username": username,
                    "email": email,
                    "user_id": user_id,
                    "user_type": user_type,
                }
            )

        except Exception as e:
            print("❌ Error in Work_from_home_accept:", e)

    return render(
        request,
        'Admin/acceptWFH.html',
        {
            "username": username,
            "email": email,
            "user_id": user_id,
            "user_type": user_type,
        }
    ) 

def update_action_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request_id = data.get('requestId')
        action = data.get('action')
        Employee_Id=data.get('EmployeeId')
        # Perform actions based on request_id and action
        print("the status_action n req_id n employee_id.....",action,request_id,Employee_Id)
        Data = {
             'Action_Status':action,
             'request_id':request_id
                }
        flask_url = "http://localhost:5000/update_work_from_home"
        response = requests.post(flask_url, json=Data)
        if response.status_code == 200:
               print(f'Request {request_id} {action}ed')
               
        # Return success response
        return JsonResponse({'message': 'Action status updated successfully'})
    else:
        # Return error response for unsupported method
        return JsonResponse({'error': 'Method not allowed'}, status=405)

   


# ── WFH date helper ──────────────────────────────────────────────────────
def _normalise_wfh(records):
    """Normalise date strings and field names for WFH records."""
    out = []
    for item in records:
        for f in ('Applied_on', 'Start_Date', 'End_Date'):
            v = item.get(f, '')
            if v and hasattr(v, 'strftime'):
                item[f] = v.strftime('%Y-%m-%d')
            elif v:
                item[f] = safe_date(str(v))
        if 'Status' not in item:
            item['Status'] = 'Waiting'
        out.append(item)
    return out


@login_required
def wfh_accept(request, request_id, *args, **kwargs):
    """Accept a WFH request. Also handles legacy Work_From_Home_Action URL."""
    session_user = get_session_user(request)
    allowed = ["employer", "manager", "team lead", "teamlead", "admin"]
    if not session_user or session_user['user_type'].lower() not in allowed:
        return HttpResponse("Unauthorized", status=403)
    try:
        requests.post(
            "http://localhost:5000/update_work_from_home",
            json={"Action_Status": "accept", "request_id": str(request_id)}
        )
        print(f"✅ WFH {request_id} accepted by {session_user['username']}")
    except Exception as e:
        print("WFH accept error:", e)
    return redirect('get_Employee_WFHInfo')


@login_required
def wfh_reject(request, request_id, *args, **kwargs):
    """Reject a WFH request. Also handles legacy Work_From_Home_Action URL."""
    session_user = get_session_user(request)
    allowed = ["employer", "manager", "team lead", "teamlead", "admin"]
    if not session_user or session_user['user_type'].lower() not in allowed:
        return HttpResponse("Unauthorized", status=403)
    try:
        requests.post(
            "http://localhost:5000/update_work_from_home",
            json={"Action_Status": "reject", "request_id": str(request_id)}
        )
        print(f"❌ WFH {request_id} rejected by {session_user['username']}")
    except Exception as e:
        print("WFH reject error:", e)
    return redirect('get_Employee_WFHInfo')


@login_required
def Work_From_Home_Action(request, Request_id, username=None, user_type=None,
                          email=None, user_id=None, action='accept'):
    """Legacy URL handler — routes to wfh_accept or wfh_reject."""
    if action == 'accept':
        return wfh_accept(request, Request_id)
    else:
        return wfh_reject(request, Request_id)


@login_required
def get_Employee_WFHInfo(request, *args, **kwargs):
    # *args/**kwargs absorb any legacy URL parameters that may still be routed here
    session_user = get_session_user(request)

    if not session_user or not session_user.get('user_type'):
        return redirect('login')

    if session_user['user_type'].lower() != "employer":
        return HttpResponse("Unauthorized", status=403)

    # ── Always fetch employee count + names + all pending WFH on GET ──
    base = requests.post("http://localhost:5000/get_employees_count",
                         json={"request_type": "get_employess"})

    Employee_Count = None
    All_Names_Ids  = []
    Work_From_Home_Info = []
    Employee_ID    = None
    Employee_Name  = None
    date_filter    = None

    if base.status_code == 200:
        base_data = base.json()
        try:
            Employee_Count = int(base_data['Total_employees'][0]['COUNT(Employee_id)'])
            All_Names_Ids  = base_data['all_employee_name_id']
        except Exception as e:
            print("WFH base parse error:", e)

    if request.method == "POST":
        name_input  = request.POST.get("nameInput", "").strip()
        date_filter = request.POST.get("dateFilter", "").strip() or None

        if not name_input:
            # No employee selected — show all pending
            Work_From_Home_Info = _normalise_wfh(
                base_data.get('Work_From_Home_Info', []) if base.status_code == 200 else []
            )
        else:
            parts = name_input.split()
            Employee_ID   = parts[0] if parts else ""
            Employee_Name = parts[1] if len(parts) > 1 else ""
            try:
                r2 = requests.post("http://localhost:5000/get_employee_WFH_Info",
                                   json={"employee_id": Employee_ID})
                if r2.status_code == 200:
                    raw = r2.json().get('employee_Emp_WHF_Info', [])
                    Work_From_Home_Info = _normalise_wfh(raw)
                    # Client-side date filter
                    if date_filter and Work_From_Home_Info:
                        Work_From_Home_Info = [
                            w for w in Work_From_Home_Info
                            if w.get('Start_Date', '') <= date_filter <= w.get('End_Date', '')
                        ]
            except Exception as e:
                print("WFH search error:", e)
    else:
        # GET — show all pending WFH from get_employees_count
        Work_From_Home_Info = _normalise_wfh(
            base_data.get('Work_From_Home_Info', []) if base.status_code == 200 else []
        )

    return render(request, "Admin/WFH.html", {
        **session_user,
        "Work_From_Home_Info": Work_From_Home_Info,
        "Employee_ID":    Employee_ID,
        "Employee_Name":  Employee_Name,
        "Employee_Count": Employee_Count,
        "All_Names_Ids":  All_Names_Ids,
        "date_filter":    date_filter,
    })


def get_Employee_status(request,username,user_type,email,user_id):
    if request.method=="POST":
        name_input=request.POST.get("nameInput")
        user_id=name_input.split(" ")[0]
        user_name=name_input.split(" ")[1]
        print("nameInput",user_id)
        
        flask_search="http://localhost:5000/get_employee_status_Info"
        data={
            "employee_id":user_id
        }
        response=requests.post(flask_search,json=data)
        response_data=response.json()
        if response.status_code==200:
            
            print("response is ",response_data)
            print("upto this...................")
            print(response_data['employee_Emp_Status_Info'])

            try:
                Employee_Count=response_data['Total_employees'][0]['COUNT(Employee_id)']
                print(".................................employee count..................",Employee_Count)
                All_Names_Ids=response_data['all_employee_name_id']
                print(".................................All_Names_Ids..................",All_Names_Ids)

                print("...........................................................")
                Employee_Name=response_data['employee_Emp_Status_Info'][0]['Employee_Name']

                print("employee name is",Employee_Name)
                Employee_ID=response_data['employee_Emp_Status_Info'][0]['Employee_id']
                print("employee_id...............",Employee_ID)
                print(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,")
                print("employee status info",response_data['employee_Emp_Status_Info'][0])
                employee_Emp_Status_Info=response_data['employee_Emp_Status_Info']
                print(employee_Emp_Status_Info)  
                for i in range(len(employee_Emp_Status_Info)):
                  input_date = datetime.strptime(employee_Emp_Status_Info[i]['Date'], "%a, %d %b %Y %H:%M:%S %Z")
                  Date = input_date.strftime("%Y-%m-%d")
                  employee_Emp_Status_Info[i]['Date'] = Date
                print("...")
                return render(request,'Admin/status.html',{"employee_Emp_Status_Info":employee_Emp_Status_Info,"Employee_ID":Employee_ID,
                                                     "username":username,'email':email,'user_id':user_id,'user_type':user_type,"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,"Employee_Name":Employee_Name})
            except Exception as e:
                Employee_Name=user_name
                Employee_ID=user_id
                Employee_Count=response_data['Total_employees'][0]['COUNT(Employee_id)']
                All_Names_Ids=response_data['all_employee_name_id']
                print("error occuring  may be data not found",e)
                return render(request,'Admin/status.html',{"Employee_ID":Employee_ID,
                                                     "username":username,'email':email,'user_id':user_id,'user_type':user_type,"Employee_Count":Employee_Count,"All_Names_Ids":All_Names_Ids,"Employee_Name":Employee_Name})
        else:
            print("data is not going",response.status_code)
    return render(request,"Admin/status.html",{"username":username,'email':email,'user_id':user_id,'user_type':user_type})


@login_required
def AdminStatusInfo(request):

    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    if session_user['user_type'].lower() != "employer":
        return HttpResponse("Unauthorized", status=403)

    # Handle search POST from the status page itself
    if request.method == "POST":

        name_input  = request.POST.get("nameInput", "").strip()
        date_filter = request.POST.get("dateFilter", "").strip()   # NEW

        if name_input:
            parts = name_input.split()
            selected_emp_id   = parts[0] if len(parts) > 0 else ""
            selected_emp_name = parts[1] if len(parts) > 1 else ""

            flask_search = "http://localhost:5000/get_employee_status_Info"
            payload = {"employee_id": selected_emp_id}
            if date_filter:
                payload["date_filter"] = date_filter

            try:
                response      = requests.post(flask_search, json=payload)
                response_data = response.json()

                Employee_Count          = response_data['Total_employees'][0]['COUNT(Employee_id)']
                All_Names_Ids           = response_data['all_employee_name_id']
                employee_Emp_Status_Info = response_data.get('employee_Emp_Status_Info', [])

                for item in employee_Emp_Status_Info:
                    try:
                        item['Date'] = datetime.strptime(
                            item['Date'], "%a, %d %b %Y %H:%M:%S %Z"
                        ).strftime("%Y-%m-%d")
                    except:
                        pass

                # client-side date filter fallback
                if date_filter and employee_Emp_Status_Info:
                    employee_Emp_Status_Info = [
                        r for r in employee_Emp_Status_Info
                        if str(r.get('Date', ''))[:10] == date_filter
                    ]

                Employee_Name = employee_Emp_Status_Info[0]['Employee_Name'] if employee_Emp_Status_Info else selected_emp_name
                Employee_ID   = employee_Emp_Status_Info[0]['Employee_id']   if employee_Emp_Status_Info else selected_emp_id

                return render(request, 'Admin/status.html', {
                    **session_user,
                    "employee_Emp_Status_Info": employee_Emp_Status_Info,
                    "Employee_ID":    Employee_ID,
                    "Employee_Name":  Employee_Name,
                    "Employee_Count": Employee_Count,
                    "All_Names_Ids":  All_Names_Ids,
                    "date_filter":    date_filter,
                })
            except Exception as e:
                print("Error in AdminStatusInfo POST:", e)

    # Default GET — load employee list
    flask_url = "http://localhost:5000/get_employees_count"
    data      = {"request_type": "get_employess"}

    try:
        response      = requests.post(flask_url, json=data)

        if response.status_code != 200:
            return render(request, 'Admin/status.html', session_user)

        response_data    = response.json()
        Employee_Count   = response_data.get('Total_employees', [{}])[0].get('COUNT(Employee_id)', 0)
        All_Names_Ids    = response_data.get('all_employee_name_id', [])
        Daily_Status_Info = response_data.get('Daily_Status_Info', [])

        return render(request, 'Admin/status.html', {
            **session_user,
            "Employee_Count":    Employee_Count,
            "All_Names_Ids":     All_Names_Ids,
            "Daily_Status_Info": Daily_Status_Info,
        })

    except Exception as e:
        print("Error in AdminStatusInfo GET:", e)

    return render(request, 'Admin/status.html', session_user)


#.....................................MyTeams................................................#

@login_required
def Admin_MyTeam_Info(request):
    print("Done...................................")

    print("Done...................................")
    session_user = get_session_user(request)
    Employee_email = session_user.get("email")
    print(Employee_email)
    if not session_user:
        return redirect('login')

    # 🔐 Only Employer should access
    if session_user['user_type'].lower() != "employer":
        return HttpResponse("Unauthorized", status=403)
    data={
        "Team_lead_email":Employee_email
    }
    flask_url = 'http://localhost:5000/Myteam_info'

    try:
        response = requests.post(flask_url, json=data)

        if response.status_code != 200:
            print("Flask error:", response.status_code)
            return render(request, 'Admin/MyTeam_Info.html', session_user)

        response_data = response.json()
        MyTeam_Info = response_data.get('MyTeam_Info', [])

    except Exception as e:
        print("Flask request failed:", e)
        MyTeam_Info = []

    return render(
        request,
        'Admin/MyTeam_Info.html',
        {
            **session_user,
            "MyTeam_Info": MyTeam_Info
        }
    )

@login_required
def Announcements_Data(request):

    # 🔐 GET USER FROM SESSION
    user = get_session_user(request)
    username  = user['username']
    email     = user['email']
    user_id   = user['user_id']
    user_type = user['user_type']

    # ================= POST: CREATE ANNOUNCEMENT =================
    if request.method == "POST":
        Announcement_date = request.POST.get('Announcement_date')
        Announcement = request.POST.get('Announcement')

        data = {
            "Employee_id": user_id,
            "Employee_Name": username,
            "Announcement_date": Announcement_date,
            "Announcement": Announcement
        }

        flask_url = "http://localhost:5000/announcement"
        response = requests.post(flask_url, json=data)

        if response.status_code == 200:
            response_data = response.json()
            Announcement_Info = response_data.get('Announcement_Info', [])

            # 🔄 Format dates
            for ann in Announcement_Info:
                input_date = datetime.strptime(
                    ann['Announcement_date'],
                    "%a, %d %b %Y %H:%M:%S %Z"
                )
                ann['Announcement_date'] = input_date.strftime("%Y-%m-%d")

            return render(
                request,
                'user/Anouncements.html',
                {
                    "Announcement_Info": Announcement_Info,
                    "username": username,
                    "email": email,
                    "user_id": user_id,
                    "user_type": user_type
                }
            )

    # ================= GET: FETCH ANNOUNCEMENTS =================
    flask_url = "http://localhost:5000/Announcement_Info"
    response = requests.post(flask_url, json={"request": ""})

    if response.status_code == 200:
        response_data = response.json()
        Announcement_Info = response_data.get('Announcement_Info', [])

        # 🔄 Format dates
        for ann in Announcement_Info:
            input_date = datetime.strptime(
                ann['Announcement_date'],
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            ann['Announcement_date'] = input_date.strftime("%Y-%m-%d")

        # 🔀 Role-based template
        if user_type.lower() == "employee":
            template = 'user/Anouncements.html'
        else:
            template = 'Admin/AdminAnnouncement.html'

        return render(
            request,
            template,
            {
                "Announcement_Info": Announcement_Info,
                "username": username,
                "email": email,
                "user_id": user_id,
                "user_type": user_type
            }
        )

    # ================= FALLBACK =================
    return render(
        request,
        'user/Anouncements.html',
        {
            "username": username,
            "email": email,
            "user_id": user_id,
            "user_type": user_type
        }
    )





def Announcements_admin(request,username,user_type,email,user_id):
    if request.method=="POST":
        Announcement_date = request.POST.get('Announcement_date')
        Announcement = request.POST.get('Announcement')
        
        data={
            "Employee_id":user_id,
            "Employee_Name":username,
            "Announcement_date":Announcement_date,
            "Announcement":Announcement

        }
        flask_url="http://localhost:5000/announcement"
        response=requests.post(flask_url,json=data)
        if response.status_code==200:
            response_data=response.json()
            Announcement_Info=response_data['Announcement_Info']
            print("response data from announcement is",Announcement_Info)
            for i in range(len(Announcement_Info)):
                input_date = datetime.strptime(Announcement_Info[i]['Announcement_date'], "%a, %d %b %Y %H:%M:%S %Z")
                Date = input_date.strftime("%Y-%m-%d")
                Announcement_Info[i]['Announcement_date'] = Date
                # Assuming Announcement_Info is a list of dictionaries
                for announcement in Announcement_Info:
                    announcement_date = announcement['Announcement_date']
    # Now you can use announcement_date as needed

                    print(f"Announcement Date: {announcement_date}")
            return render(request,'Admin/AdminAnnouncement.html',{"Announcement_date":Announcement_date,"Announcement_Info":Announcement_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
        else:
            print("data not going")
        
        return render(request,'Admin/AdminAnnouncement.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type})
    flask_url="http://localhost:5000/Announcement_Info"
    data = {
            'request':""
        }  
    response=requests.post(flask_url,json=data)
    if response.status_code==200:
            response_data=response.json()
            Announcement_Info=response_data['Announcement_Info']
            print("response data from announcement_info is",Announcement_Info)
            for i in range(len(Announcement_Info)):
                input_date = datetime.strptime(Announcement_Info[i]['Announcement_date'], "%a, %d %b %Y %H:%M:%S %Z")
                Date = input_date.strftime("%Y-%m-%d")
                Announcement_Info[i]['Announcement_date'] = Date
            return render(request,'Admin/AdminAnnouncement.html',{"Announcement_Info":Announcement_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
    else:
        print("data not going")
        
        return render(request,'Admin/AdminAnnouncement.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type})



@login_required
def delete_announcement_view(request, Announcement_date, Announcement):

    print("delete_announcement_view called")

    session_user = get_session_user(request)

    if not session_user:
        return redirect("login")

    username = session_user['username']
    email = session_user['email']
    user_type = session_user['user_type']
    user_id = session_user['user_id']

    flask_url = "http://localhost:5000/delete_announcement"

    data = {
        "Employee_id": user_id,
        "user_type": user_type,
        "Announcement": Announcement,
        "Announcement_date": Announcement_date
    }

    try:
        response = requests.post(flask_url, json=data)

        if response.status_code != 200:
            print("Flask error:", response.status_code)
            return render(
                request,
                'Admin/AdminAnnouncement.html',
                session_user
            )

        response_data = response.json()
        Announcement_Info = response_data.get('Announcement_Info', [])

    except Exception as e:
        print("Flask request failed:", e)
        return render(
            request,
            'Admin/AdminAnnouncement.html',
            session_user
        )

    # ---------------------------------------
    # Safe Date Formatting
    # ---------------------------------------
    for item in Announcement_Info:
        try:
            input_date = datetime.strptime(
                item.get('Announcement_date'),
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            item['Announcement_date'] = input_date.strftime("%Y-%m-%d")
        except:
            pass

    # ---------------------------------------
    # Render Based on User Type
    # ---------------------------------------
    if user_type.lower() == "employee":
        return render(
            request,
            'user/Anouncements.html',
            {
                **session_user,
                "Announcement_Info": Announcement_Info,
                "Announcement_date": Announcement_date
            }
        )

    else:
        return render(
            request,
            'Admin/AdminAnnouncement.html',
            {
                **session_user,
                "Announcement_Info": Announcement_Info,
                "Announcement_date": Announcement_date
            }
        )
def Announcement(request,Date,username,user_type,email,user_id,):
    print("calling this funtion",Date)
    print('------------------') 
    data={
        "Selected_Date":Date,
        "username":username,
        "user_id":user_id,        
    }
    print("...............",Date)
    flask_url="http://localhost:5000/Announcement"
    response=requests.post(flask_url,json=data)
    flask_response=response.json()
    Announcement_Info=flask_response['Announcement_Info']
    # input_date = datetime.strptime(Announcement_Info[0]['Date'] , "%a, %d %b %Y %H:%M:%S %Z")
    # Date = input_date.strftime("%Y-%m-%d")
    # Announcement_Info[0]['Date']=Date
    # Clock_In=Announcement_Info[0]['clock_in_time']
    # Clock_Out=Announcement_Info[0]['clock_out_time']

    print(Date)
    print(flask_response)
    if response.status_code==200:
        try:
            return render(request,'user/Anouncements.html',{"Announcement_Info":Announcement_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
        except:
            print("error coming in status function")
            return render(request,'user/Anouncements.html',{"Announcement_Info":Announcement_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
  
    else:
        print('Failed to fetch details')
    return render(request,'user/Anouncements.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type,})





# def Announcement_Update(request,Date,username,user_type,email,user_id,):
#     print("calling this funtion")
#     if request.method=='POST':
#         Selected_Date=request.POST.get('date')
#         Selected_Announcement=request.POST.get('Announcement')
#         # Insert_Date=request.post('Insert_Date')
#         print(Selected_Date,Selected_Announcement)
#         empid=user_id
#         empname=username
#         email=email
#         user_type=user_type
#         print("this is empid, empname and email",empid, empname, email, user_type) 
#         Data={
#             'employeeid':empid,
#             'user_type':user_type,
#             'email':email,
#             'Selected_Announcement':Selected_Announcement,
#             'date':Selected_Date,
#         }
#         flask_url="http://localhost:5000/Announcement_Update"
#         response=requests.post(flask_url,json=Data)
#         flask_response=response.json()
#         print(flask_response)
#         if response.status_code==200:
#             Announcement_Info=flask_response['Announcement_Info']
#             # Announcement_Info=flask_response['Announcement_Info']

#             print("response data from announcement is",Announcement_Info)
#             for i in range(len(Announcement_Info)):
#                 input_date = datetime.strptime(Announcement_Info[i]['Announcement_date'], "%a, %d %b %Y %H:%M:%S %Z")
#                 Date = input_date.strftime("%Y-%m-%d")
#                 Announcement_Info[i]['Announcement_date'] = Date

#             try:
#                 return render(request,'user/Anouncements.html',{"Announcement_Info":Announcement_Info, "Date":Selected_Date,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
#             except:
#                 print("error coming in status function")
#                 return render(request,'user/Anouncements.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type,})

#     else:
#         print('Failed to fetch details')
#     return render(request,'user/Anouncements.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type,})


@login_required
def Announcement_Update(request, Date):

    print("Announcement_Update called")

    session_user = get_session_user(request)

    if not session_user:
        return redirect("login")

    username = session_user['username']
    email = session_user['email']
    user_type = session_user['user_type']
    user_id = session_user['user_id']

    # ------------------------------------
    # POST → Update Announcement
    # ------------------------------------
    if request.method == 'POST':

        selected_date = request.POST.get('date')
        selected_announcement = request.POST.get('Announcement')

        print("Selected:", selected_date, selected_announcement)

        flask_url = "http://localhost:5000/Announcement_Update"

        data = {
            'employeeid': user_id,
            'user_type': user_type,
            'email': email,
            'Selected_Announcement': selected_announcement,
            'date': selected_date,
        }

        try:
            response = requests.post(flask_url, json=data)

            if response.status_code != 200:
                print("Flask error:", response.status_code)
                return render(
                    request,
                    'Admin/AdminAnnouncement.html',
                    session_user
                )

            flask_response = response.json()
            Announcement_Info = flask_response.get('Announcement_Info', [])

        except Exception as e:
            print("Flask request failed:", e)
            return render(
                request,
                'Admin/AdminAnnouncement.html',
                session_user
            )

        # ------------------------------------
        # Format Dates Safely
        # ------------------------------------
        for item in Announcement_Info:
            try:
                input_date = datetime.strptime(
                    item.get('Announcement_date'),
                    "%a, %d %b %Y %H:%M:%S %Z"
                )
                item['Announcement_date'] = input_date.strftime("%Y-%m-%d")
            except:
                pass

        # ------------------------------------
        # Render Based on User Type
        # ------------------------------------
        if user_type.lower() == "employee":
            return render(
                request,
                'user/Anouncements.html',
                {
                    **session_user,
                    "Announcement_Info": Announcement_Info,
                    "Date": selected_date
                }
            )

        else:
            return render(
                request,
                'Admin/AdminAnnouncement.html',
                {
                    **session_user,
                    "Announcement_Info": Announcement_Info,
                    "Date": selected_date
                }
            )

    # ------------------------------------
    # GET → Default Page Load
    # ------------------------------------
    return render(
        request,
        'Admin/AdminAnnouncement.html',
        session_user
    )


print('update hit 1 !!!!!!!!!!')
@login_required
def update_announce(request, Selected_Date):
    print('update hit 2 !!!!!!!!!!')
    session_user = get_session_user(request)
    
    print(session_user)
    if not session_user:
        return redirect("login")

    username = session_user['username']
    email = session_user['email']
    user_type = session_user['user_type']
    user_id = session_user['user_id']

    print("Updating announcement for:", Selected_Date)

    flask_url = "http://localhost:5000/Anounce_Data"

    data = {
        "Selected_Date": Selected_Date,
        "employeeid": user_id,
        "employeename": username,
        "email": email,
        "date": Selected_Date,
    }

    try:
        response = requests.post(flask_url, json=data)

        if response.status_code != 200:
            print("Flask error:", response.status_code)
            return render(
                request,
                'update_announce.html',
                {**session_user, "Selected_Date": Selected_Date}
            )

        response_data = response.json()
        Announcement_Info = response_data.get('Announcement_Info', [])

    except Exception as e:
        print("Flask request failed:", e)
        return render(
            request,
            'update_announce.html',
            {**session_user, "Selected_Date": Selected_Date}
        )

    # ✅ Safe Date Formatting
    for item in Announcement_Info:
        try:
            input_date = datetime.strptime(
                item.get('Announcement_date'),
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            item['Announcement_date'] = input_date.strftime("%Y-%m-%d")
        except:
            # If already formatted
            pass

    selected_date = (
        Announcement_Info[0]['Announcement_date']
        if Announcement_Info else Selected_Date
    )

    return render(
        request,
        'update_announce.html',
        {
            **session_user,
            "Announcement_Info": Announcement_Info,
            "Selected_Date": selected_date
        }
    )




def Clock_Adjustment(request,request_type,username,user_type,email,user_id):
    print("................................")
    try:
        if request.method == "POST":
            if request_type == "Attendance":
                Selected_Date=request.POST.get('Date')
                Clock_In=request.POST['clock_in']
                Clock_Out=request.POST['clock_out']
                Reason=request.POST.get('Reason')
                print("dates are",Clock_In,Clock_Out,Selected_Date,Reason)
                print("................................")
            
                data={
                    "Clock_In":Clock_In,
                    "Clock_Out":Clock_Out,
                    "username":username,
                    "id":user_id,
                    "Selected_Date":Selected_Date,
                    "Reason":Reason, 
                    "Request_Type":"Attendance"   
                }
            
            elif request_type=="Partial":
                Selected_Date=request.POST.get('Date')
                Time_of_Day=request.POST.get('Time_of_Day')
                Reason=request.POST.get('Reason')
                data={
                    "username":username,
                    "id":user_id,
                    "Selected_Date":Selected_Date,
                    "Time_of_Day":Time_of_Day,
                    "Reason":Reason,
                    "Request_Type":"Partial"    
                }
            elif request_type=="Wfh":
                Selected_Date=request.POST.get('Date')
                Reason=request.POST.get('Reason')
                data={
                    "username":username,
                    "id":user_id,
                    "Selected_Date":Selected_Date,
                    "Reason":Reason,
                    "Request_Type":"Wfh"    
                }
            elif request_type=="Leave":
                Selected_Date=request.POST.get('Date')
                Reason=request.POST.get('Reason')
                data={
                    "username":username,
                    "id":user_id,
                    "Selected_Date":Selected_Date,
                    "Reason":Reason,
                    "Request_Type":"Leave"    
                }
            flask_url="http://localhost:5000/Clock_Adjust"
            response=requests.post(flask_url,json=data)
        try:
            if response.status_code==200:
                response_data=response.json()
                print("getting data",response_data)
                # Attendance_data=response_data['Attendance_data']
                # for i in range(len(Attendance_data)):
                #  input_date= datetime.strptime(Attendance_data[i]['Date'] , "%a, %d %b %Y %H:%M:%S %Z")
                #  Date1 = input_date.strftime("%Y-%m-%d")
                #  Attendance_data[i]['Date']=Date1
                Attendance_data=""
                return render(request,'user/clock.html',{"Attendance_data":Attendance_data,"username":username,'email':email,'user_id':user_id,'user_type':user_type})

            else:
                print("data is not going",response.status_code)
        except:
            return render(request,'user/clock.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type})  
    except Exception as e:
        print("error is",e)


def ClockAdj_Data(request,Date,username,user_type,email,user_id,):
    print("calling this funtion",Date)
    print('------------------') 
    data={
        "Selected_Date":Date,
        "username":username,
        "user_id":user_id,        
    }
    print("...............",Date)
    flask_url="http://localhost:5000/Get_ClockAdj"
    response=requests.post(flask_url,json=data)
    flask_response=response.json()
    Clock_Info=flask_response['Clock_Info']
    input_date = datetime.strptime(Clock_Info[0]['Date'] , "%a, %d %b %Y %H:%M:%S %Z")
    Date = input_date.strftime("%Y-%m-%d")
    Clock_Info[0]['Date']=Date
    Clock_In=Clock_Info[0]['clock_in_time']
    Clock_Out=Clock_Info[0]['clock_out_time']

    print(Date)
    print(flask_response)
    if response.status_code==200:
        try:
            return render(request,'user/clockAdjust.html',{"Date":Date,"Clock_Info":Clock_Info,"Clock_In":Clock_In,"Clock_Out":Clock_Out,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
        except:
            print("error coming in status function")
            return render(request,'user/clockAdjust.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type,})
    
    else:
        print('Failed to fetch details')
    return render(request,'user/clockAdjust.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type,})



@login_required
def profile(request):
    # 🔑 Read logged-in user from session
    session_user = get_session_user(request)

    user_id = session_user['user_id']
    print("user_id is", user_id)

    flask_url = "http://localhost:5000/profile"

    # Send request to Flask
    response = requests.post(
        flask_url,
        json={"employee_id": user_id}
    )

    Profile_Info = {}

    if response.status_code == 200:
        response_data = response.json()
        print("profile information is....", response_data)

        Profile_Info = response_data.get('Profile_Info', {})

    else:
        print("error is", response.status_code)

    # 🧠 Single render path (important)
    return render(
        request,
        'user/profile.html',
        {
            **session_user,        # username, email, user_id, user_type
            "Profile_Info": Profile_Info
        }
    )    


def notification_Data(request, username, email, user_id, user_type):
    print("this is notification_data")
    flask_url = 'http://localhost:5000/notification'
    data={
        "user_id":user_id, 
        "username":username
        }
    response=requests.post(flask_url, json=data)
    if response.status_code==200:
        response_data=response.json()
        Birthday_Info=response_data["Birthday_Info"]
        print("response data from birthday_info is",Birthday_Info)
        for i in range(len(Birthday_Info)):
            input_date = datetime.strptime(Birthday_Info[i]['Wished_On'], "%a, %d %b %Y %H:%M:%S %Z")
            Date = input_date.strftime("%Y-%m-%d")
            Birthday_Info[i]['Wished_On'] = Date
        return render(request,'user/notification.html',{"Birthday_Info":Birthday_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
    
    else:
        print("data not going")
        
        return render(request,'user/notification.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type})


def Birthday_Data(request):
    print("this is Birthday_Data function in views")
    try:
        username=request.POST.get('username')
        userid=request.POST.get('userid')
        print(userid)
        print("username is:", username)
        employee_name = request.POST.get('employee_name')
        print("employee_name of employee", employee_name)
        wish = request.POST.get('wish')

        data={
            'employee_id': userid,
            'employee_name':employee_name,
            'wish':wish,
            'username':username,

        }
            # date_of_birth = data.get('date_of_birth')
        print("this is above flask print")
        flask_url="http://localhost:5000/Birthday"
        response=requests.post(flask_url,json=data)
        if response.status_code==200:
            response_data=response.json()
            Announcement_Info=response_data.get('Announcement_Info',[])

            print("response data from announcement is",Announcement_Info)

            for i in Announcement_Info:
                input_date = datetime.strptime(i['inserting_date'], "%a, %d %b %Y %H:%M:%S %Z")
                # Date = input_date.strftime("%Y-%m-%d")
                i['inserting_date'] = input_date.strftime("%Y-%m-%d")
            return JsonResponse({"status": "success", "Announcement_Info": Announcement_Info})
        
        else:
            print("data not going")
            return JsonResponse({"status": "error", "message": "Flask service returned error"}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)
    
@login_required
def Queries_Data(request):

    session_user = get_session_user(request)

    if not session_user:
        return redirect('login')

    user_id = session_user['user_id']
    username = session_user['username']
    email = session_user['email']
    user_type = session_user['user_type']

    # ==================================================
    # 🔵 EMPLOYER VIEW
    # ==================================================
    if user_type.lower() == "employer":

        flask_url = "http://localhost:5000/Queries_Info"
        response = requests.post(flask_url, json={"request": "all"})

        if response.status_code == 200:
            data = response.json()
            Queries_Info = data.get("Queries_Info", [])

            # Format Date safely
            for q in Queries_Info:
                try:
                    q['Date'] = q['Date'].strftime("%Y-%m-%d")
                except:
                    pass

            return render(
                request,
                'Admin/employer_queries.html',
                {
                    **session_user,
                    "Queries_Info": Queries_Info
                }
            )

        return render(request, 'Admin/employer_queries.html', session_user)

    # ==================================================
    # 🟢 EMPLOYEE SUBMIT QUERY (POST)
    # ==================================================
    if request.method == "POST":

        query_text = request.POST.get('Query')

        data = {
            "Employee_id": user_id,
            "Employee_Name": username,
            "Employee_Email": email,
            "Query": query_text
        }

        flask_url = "http://localhost:5000/query"
        requests.post(flask_url, json=data)

        # 🔁 After insert → reload page (important!)
        return redirect("Queries_Data")

    # ==================================================
    # 🟢 EMPLOYEE GET → FETCH ONLY THEIR QUERIES
    # ==================================================
    flask_url = "http://localhost:5000/Queries_Info"

    response = requests.post(flask_url, json={
        "employee_id": user_id,
        "request": "employee"
    })
    print(response.json())
    Queries_Info = []

    if response.status_code == 200:
        data = response.json()
        Queries_Info = data.get("Queries_Info", [])

    return render(
        request,
        'user/Query.html',
        {
            **session_user,
            "Queries_Info": Queries_Info
        }
    )
@login_required
def reply_query(request, query_id):
    session_user = get_session_user(request)

    if request.method == "POST":
        answer = request.POST.get("answer")

        flask_url = "http://localhost:5000/reply_query"
        requests.post(flask_url, json={
            "query_id": query_id,
            "answer": answer
        })

        return redirect("Queries_Data")

    return render(request, "Admin/reply_query.html", {
        **session_user,
        "query_id": query_id
    })

def Admin_notification_Data(request, username, email, user_id, user_type):
    print("calling admin notification")
    if request.method== "POST":
        Date = request.POST.get('Date')
        Query = request.POST.get('Query')
        
    data={
            "Employee_id": user_id,
            "Employee_Name":username,
            "Employee_Email":email,    
        }
    flask_url="http://localhost:5000/admin_notification"
    print(f"Sending POST request to {flask_url} with data: {data}")
    response=requests.post(flask_url, json=data)
    if response.status_code==200:
            response_data=response.json()
            Queries_Info=response_data["Queries_Info"]
            print("response data from Queries_Info is",Queries_Info)
            for i in range(len(Queries_Info)):
                input_date = datetime.strptime(Queries_Info[i]['Date'], "%a, %d %b %Y %H:%M:%S %Z")
                Date = input_date.strftime("%Y-%m-%d")
                Queries_Info[i]['Date'] = Date
            return render(request,'Admin/Admin_Notification.html',{"Queries_Info":Queries_Info,"username":username,'email':email,'user_id':user_id,'user_type':user_type})
    
    else:
            print("data not going")
            return render(request,'Admin/Admin_Notification.html',{"username":username,'email':email,'user_id':user_id,'user_type':user_type})
@login_required
def admin_chatbot(request):
    """Admin chatbot page — renders the chatbot UI."""
    session_user = get_session_user(request)
    if session_user['user_type'].lower() != 'employer':
        return HttpResponse("Unauthorized", status=403)
    return render(request, 'Admin/chatbot.html', session_user)

from django.http import HttpResponse

def Pdf_Download(request, *args, **kwargs):
    return HttpResponse("PDF download temporarily disabled")

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .chatbot_engine import process_query

@csrf_exempt
@login_required
def chatbot_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        message = data.get("message", "")
        user_id = request.session.get("user_id")   # ← add this
        reply = process_query(message, user_id)     # ← pass it
        return JsonResponse({"reply": reply})
    return JsonResponse({"error": "Method not allowed"}, status=405)