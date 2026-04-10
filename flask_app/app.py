from flask import Flask,request,jsonify,render_template_string
import pymysql.cursors
import requests
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from flask import Flask,render_template,redirect,url_for,request,flash
import random
import string
import uuid
from Database_schema import create_table_query_UsersData,create_table_query_employee_attendance,create_table_holiday,create_table_Announcement,create_table_work_from_Home,create_table_Query
from Database_schema import create_table_query_employee,create_table_leave_request,create_table_daily_status,create_table_leave_balance,create_table_leave_history, create_table_query_birthday_wish
from Database_schema import create_table_Clock_Adj
from flask_mail import Mail, Message
from datetime import datetime,timedelta,date
app = Flask(__name__)


print(" FLASK /login HIT ")
# Configure mail server
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = 'suckerpunchjohnwick007@gmail.com'
app.config['MAIL_USERNAME'] = 'enerziff@gmail.com'
app.config['MAIL_PASSWORD'] = 'qjts fwqq qgtn hbjt'
# app.config['MAIL_PASSWORD'] = 'ilkv wibm olar coow'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)



#database connection with pymysql..........
MYSQL_HOST = "127.0.0.1"
MYSQL_USER = "root"
MYSQL_PASSWORD = "shashi14"
MYSQL_DB = "payroll_project"
connection = pymysql.connect(host=MYSQL_HOST,
                             user=MYSQL_USER,
                             password=MYSQL_PASSWORD,
                             db=MYSQL_DB,
                             cursorclass=pymysql.cursors.DictCursor)



# creating table (employee_complete_details) into database
with connection.cursor() as cursor:
    cursor.execute("SELECT DATABASE()")
    print("CONNECTED DB:", cursor.fetchone())

with connection.cursor() as cursor:
    cursor.execute(create_table_query_employee)
    connection.commit()
with connection.cursor() as cursor:
    cursor.execute(create_table_Clock_Adj)
    # print(create_table_Clock_Adj)
    connection.commit()
#creating table(users_Register_Data) into database
with connection.cursor() as cursor:
        cursor.execute(create_table_query_UsersData)
        connection.commit()

#creating table(Employee_Attendance_Data) into database
with connection.cursor() as cursor:
     cursor.execute(create_table_query_employee_attendance)
     connection.commit()

with connection.cursor() as cursor:
     cursor.execute(create_table_daily_status)
     connection.commit()

#creating table(Leave_Request) into database
with connection.cursor() as cursor:
     cursor.execute(create_table_leave_request)
     connection.commit()

#creating table(Leave_history) into database
with connection.cursor() as cursor:
    cursor.execute(create_table_leave_history)
    connection.commit()

#creating table for leave_balance........
with connection.cursor() as cursor:
    cursor.execute(create_table_leave_balance)
    connection.commit()

with connection.cursor() as cursor:
     cursor.execute(create_table_Announcement)
     connection.commit()

with connection.cursor() as cursor:
    cursor.execute(create_table_holiday)
    connection.commit()

with connection.cursor() as cursor:
    cursor.execute(create_table_work_from_Home)
    connection.commit()

with connection.cursor() as cursor:
    cursor.execute(create_table_query_birthday_wish)
    connection.commit()

with connection.cursor() as cursor:
    cursor.execute(create_table_Query)
    connection.commit()




@app.route('/employee_complete_details', methods=['POST'])
def Upsert_Employee_Details():
    try:
        Data = request.get_json()
        print("......................the Data is........")
        print(Data)

        # REQUIRED FIELDS
        Employee_id = Data.get('employee_id')
        Employee_Name = Data.get('employee_name')
        Employee_email = Data.get('employee_email')
        Username = Data.get('Username')
        Password = Data.get('Password')
        usertype = Data.get('usertype')
        Request_type = Data.get('request_type')

        # 🔒 HARD VALIDATION
        if not all([Employee_id, Employee_email, Username, Password, usertype]):
            return jsonify({
                'status': 'failed',
                'message': 'missing required fields'
            })

        # Normalize usertype
        usertype = usertype.strip().capitalize()

        with connection.cursor() as cursor:

            # ================= INSERT =================
            if Request_type == 'insert':

                # ❌ Prevent duplicate employee
                cursor.execute("""
                    SELECT Employee_id 
                    FROM employee_complete_details 
                    WHERE Employee_id=%s OR Employee_email=%s
                """, (Employee_id, Employee_email))

                if cursor.fetchone():
                    return jsonify({
                        'status': 'failed',
                        'message': 'employee already exists'
                    })

                # Leave calculation
                Sick_Leave = float(Data.get('Sick_Leave', 0))
                Wedding_Leave = float(Data.get('Wedding_Leave', 0))
                Maternity_Leave = float(Data.get('Maternity_Leave', 0))
                Paternity_Leave = float(Data.get('Paternity_Leave', 0))

                No_of_Leaves = Sick_Leave + Wedding_Leave + Maternity_Leave + Paternity_Leave

                # ✅ INSERT employee_complete_details
                cursor.execute("""
                    INSERT INTO employee_complete_details (
                        Employee_id, Employee_Name, Employee_email, Gender,
                        Phone_Number, Date_of_birth, Address, Department,
                        Position, Team_lead, Team_lead_email, Date,
                        Manager_name, Manager_email, Hire_date,
                        Work_location, Skills, Emergency_contact,
                        Username, Password, usertype
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    Employee_id,
                    Employee_Name,
                    Employee_email,
                    Data.get('Gender'),
                    Data.get('Phone_Number'),
                    Data.get('Date_of_birth'),
                    Data.get('Address'),
                    Data.get('Department'),
                    Data.get('Position'),
                    Data.get('Team_lead'),
                    Data.get('Team_lead_email'),
                    Data.get('Date'),
                    Data.get('Manager_name'),
                    Data.get('Manager_email'),
                    Data.get('Hire_date'),
                    Data.get('Work_location'),
                    Data.get('Skills'),
                    Data.get('Emergency_contact'),
                    Username,
                    Password,
                    usertype
                ))

                # ✅ INSERT leave balance
                cursor.execute("""
                    INSERT INTO Leave_balance (
                        Employee_id, Employee_Name, Employee_email, Gender,
                        Sick_Leave, Wedding_Leave, Maternity_Leave,
                        Paternity_Leave, No_of_leaves,
                        Taken_leaves, Pending_leaves
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    Employee_id,
                    Employee_Name,
                    Employee_email,
                    Data.get('Gender'),
                    Sick_Leave,
                    Wedding_Leave,
                    Maternity_Leave,
                    Paternity_Leave,
                    No_of_Leaves,
                    0.0,
                    No_of_Leaves
                ))

                connection.commit()

                return jsonify({
                    'status': 'success',
                    'message': 'employee created successfully'
                })
            # ================= UPDATE =================
            elif Request_type == 'update':

                # 🔍 Check employee exists
                cursor.execute("""
                    SELECT Employee_id
                    FROM employee_complete_details
                    WHERE Employee_id = %s
                """, (Employee_id,))

                if not cursor.fetchone():
                    return jsonify({
                        'status': 'failed',
                        'message': 'employee not found'
                    })

                # ✅ UPDATE employee details
                cursor.execute("""
                    UPDATE employee_complete_details SET
                        Employee_Name=%s,
                        Employee_email=%s,
                        Gender=%s,
                        Phone_Number=%s,
                        Date_of_birth=%s,
                        Address=%s,
                        Department=%s,
                        Position=%s,
                        Team_lead=%s,
                        Team_lead_email=%s,
                        Date=%s,
                        Manager_name=%s,
                        Manager_email=%s,
                        Hire_date=%s,
                        Work_location=%s,
                        Skills=%s,
                        Emergency_contact=%s,
                        Username=%s,
                        Password=%s,
                        usertype=%s
                    WHERE Employee_id=%s
                """, (
                    Employee_Name,
                    Employee_email,
                    Data.get('Gender'),
                    Data.get('Phone_Number'),
                    Data.get('Date_of_birth'),
                    Data.get('Address'),
                    Data.get('Department'),
                    Data.get('Position'),
                    Data.get('Team_lead'),
                    Data.get('Team_lead_email'),
                    Data.get('Date'),
                    Data.get('Manager_name'),
                    Data.get('Manager_email'),
                    Data.get('Hire_date'),
                    Data.get('Work_location'),
                    Data.get('Skills'),
                    Data.get('Emergency_contact'),
                    Username,
                    Password,
                    usertype,
                    Employee_id
                ))

                connection.commit()

                return jsonify({
                    'status': 'success',
                    'message': 'employee updated successfully'
                })
        return jsonify({
            'status': 'failed',
            'message': 'invalid request_type'
        })

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({
            'status': 'failed',
            'message': str(e)
        })

@app.route("/")
def home():
    return "Flask backend is running"
#.............................................employee_details.......................................................
#sending employee_complete details present in the main table(employee_complete_details) based on the employee_id...
@app.route('/employee_details',methods=['POST'])
def Fetch_Emp_Info():
    #getting employee_id.....
    if request.method=='POST':
       Data=request.get_json()
       Employee_Id=Data['Employee_id']
       #printing employee_id from request for clarification...
       print(Data)
       with connection.cursor() as cursor:
        #selecting employee details from main table based on employee_id.....
        Select_Query='SELECT * FROM employee_complete_details WHERE Employee_id=%s'
        cursor.execute(Select_Query,Employee_Id)
        Emp_Info=cursor.fetchone()
        try:
            if Emp_Info:
                #sending employee_info in response if user exists...
                Response_Data = {'status': 'success', 'employee_complete_info':Emp_Info}
                print("employee_details basedon Employee_id  data sent  successfully")
                return jsonify(Response_Data)
            else:
                Response_Data = {'status': 'failed','message':'requested emp_id doesn"t exist in table...'}
                print("employee_id not exist..")
                return jsonify(Response_Data)
        except Exception as e:
            print("exception occured in Fetch_Emp_Info function and error is",e)
            return jsonify(Response_Data)




#............................................Admin.................................................
@app.route('/admin_edit',methods=['POST'])
def emp_id_name_email():
    if request.method=='POST':
       data=request.get_json()
    #    Employee_Id=data['Employee_id']
       print(data)
       with connection.cursor() as cursor:
            sql='SELECT Employee_id, Employee_Name,Employee_email FROM employee_complete_details '
            cursor.execute(sql)
            emp_data=cursor.fetchall()
            response_data = {'status': 'success', 'employee_complete_info':emp_data}
            print("employees_id_email,name sent  successfully")
    return jsonify(response_data)





#.....................................Insert UsersRegistersData.............................................
#receiving data from request for inserting into users_register table... 
# @app.route('/data_receive', methods=['POST'])
# def User_Register():
#     Data = request.get_json(force=True)
#     print("RAW REQUEST JSON:", Data)

#     Username = Data['username']
#     Password = Data['password']
#     Email = Data['email']
#     Usertype = Data['usertype']

#     try:
#         with connection.cursor() as cursor:

#             # 1️⃣ Insert into users_Register_Data (AUTH TABLE)
#             cursor.execute(
#                 """
#                 INSERT INTO users_Register_Data (username, email, password, usertype)
#                 VALUES (%s, %s, %s, %s)
#                 """,
#                 (Username, Email, Password, Usertype)
#             )

#             # 2️⃣ Insert into employee_complete_details (EMPLOYEE MASTER)
#             emp_id = 'EMP' + uuid.uuid4().hex[:8]
#             current_date = datetime.now().strftime('%Y-%m-%d')
#             print("executed this")
#             cursor.execute(
#                 """
#                 INSERT INTO employee_complete_details
#                 (Employee_id, Employee_Name, Employee_email, Date, Username, Password, usertype)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s)
#                 """,
#                 (emp_id, Username, Email, current_date, Username, Password, Usertype)
#             )

#             connection.commit()

#         return jsonify({
#             'status': 'success',
#             'message': 'User and employee profile created successfully',
#             'employee_id': emp_id
#         })

#     except Exception as e:
#         print("Registration error:", e)
#         return jsonify({
#             'status': 'failed',
#             'message': 'Registration failed'
#         }), 500


#...........................................SpecificInfo...........................................
def Specific_Info():
 with connection.cursor() as cursor:
    Current_Date = datetime.now().date()
    Current_Formate_Date= datetime.now().strftime('%Y-%m-%d')
    No_Of_Days=30
    New_Date_Str = Current_Date + timedelta(No_Of_Days)
    New_Date= New_Date_Str.strftime('%Y-%m-%d')
    print(Current_Date,New_Date)
    current_date_day = Current_Date.day
    current_date_month = Current_Date.month

    new_date_day = New_Date_Str.day
    new_date_month = New_Date_Str.month
    print(current_date_month,new_date_month,current_date_day,new_date_day)
#selecting emp_name and dob from main table based on specific dates(1 month).........
    # Emplyee_Complete_Details_Query='SELECT Date_of_Birth FROM employee_complete_details WHERE Date BETWEEN %s AND %s'
    # Emplyee_Complete_Details_Query='SELECT Date_of_Birth FROM employee_complete_details WHERE MONTH(Date_of_Birth) >= MONTH(CURDATE())  AND DAYOFMONTH(Date_of_Birth) >= DAYOFMONTH(CURDATE())'

    # MONTH(Current_Date) >= MONTH(New_Date)  AND DAYOFMONTH(Current_Date) >= DAYOFMONTH(New_Date)
    # cursor.execute(Emplyee_Complete_Details_Query,(Current_Formate_Date, New_Date))
    # Emp_Names_Dob_Info=cursor.fetchall()
    # print("this is date#######",Emp_Names_Dob_Info)

    Emplyee_Complete_Details_Query="SELECT Employee_Name, Date_of_birth FROM employee_complete_details WHERE (MONTH(Date_of_birth) = %s AND DAY(Date_of_birth) > %s) or (MONTH(Date_of_birth) = %s AND DAY(Date_of_birth) < %s)"
    cursor.execute(Emplyee_Complete_Details_Query,(current_date_month,current_date_day,new_date_month,new_date_day))
    Emp_Names_Dob_Info=cursor.fetchall()
    print("this is B'day date44",Emp_Names_Dob_Info)

    

#selecting emp_name and start & end dates from history table based on specific dates(1 month).........
    Current_Date = datetime.now().date()  # Current date as date object
    No_Of_Days = 30
    New_Date = Current_Date + timedelta(days=No_Of_Days) 
    Leave_history_Query='SELECT Employee_Name,Start_date,End_date FROM Leave_history WHERE Start_date BETWEEN  %s AND %s'
    cursor.execute(Leave_history_Query,(Current_Date, New_Date))
    Leave_History_Info=cursor.fetchall()
    print("this is leave history date",Leave_History_Info)

#selecting festname and holidaydate from holiday table based on specific dates(1 month).........
    Holiday_Query='SELECT Festival_name,Holiday_date FROM Holiday WHERE Holiday_date BETWEEN  %s AND %s'
    cursor.execute(Holiday_Query,(Current_Formate_Date, New_Date))
    Holiday_Info=cursor.fetchall()
    print("this is holiday date",Holiday_Info)

#selecting announcement and announcement date from announcement table based on specific dates(1 month).........
    Announcement_Query='SELECT Announcement,Announcement_date FROM Announcement WHERE Announcement_date BETWEEN  %s AND %s'
    cursor.execute(Announcement_Query,(Current_Formate_Date, New_Date))
    Announcement_Info=cursor.fetchall()
    print("this is date",Announcement_Info)

#returning the specific details based on in between dates......
    return Emp_Names_Dob_Info,Leave_History_Info,Holiday_Info,Announcement_Info




        
#..................................................Login.....................................................  
# getting data and checking login ......
# FLASK
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('username')   # email
    password = data.get('password')
    usertype = data.get('usertype')
    print(usertype)
    # print(data)
    print(email,password)
    try:
        with connection.cursor() as cursor:
            cursor.execute('select Username,usertype from employee_complete_details where usertype=%s ',(usertype))
            details=cursor.fetchall()
            print(details)
            cursor.execute("""
                SELECT Employee_id, Username, Employee_email, usertype
                FROM employee_complete_details
                WHERE Employee_email=%s
                AND Password=%s
                AND usertype=%s
            """, (email, password, usertype))

            user = cursor.fetchone()
            print(user)
        print(user)
        if not user:
            return jsonify({
                "status": "failed",
                "message": "Invalid credentials"
            }), 401

        return jsonify({
            "status": "success",
            "username": user['Username'],
            "user_id": user['Employee_id'],
            "employee_email": user['Employee_email'],
            "user_type": user['usertype']
        })
    except Exception as e:
       print("getting error at login function",str(e))
       return "error"
#not in use.................................................................
#getting data and validating email.....                      
@app.route('/validate_email', methods=['POST'])
def Validate_Email():
   if request.method=='POST':
    Data=request.get_json()
    Email=Data['email']
    print(Email)             
    # Execute the query to validate if email exists or not
    with connection.cursor() as cursor:
      Select_Query = 'SELECT Employee_email FROM employee_complete_details '
      cursor.execute(Select_Query)
      Existing_Emails = [row['email'] for row in cursor.fetchall()]
      print("exixting emails:",Existing_Emails)
# Check if the provided email exists in the list of existing emails          
      if Email in Existing_Emails:
        print("email exist")
        Response_Data = {'status': 'success', 'message': 'email exist'}
        return jsonify(Response_Data)
      else:
        print("email not exist")
        Response_Data = {'status': 'failed', 'message': 'email not exist'}
        return jsonify(Response_Data) 





#not in use.................................................................
#getting data and update password...            
@app.route('/update_password', methods=['POST'])
def Update_Password():
        if request.method == 'POST':
            Data = request.get_json()
            Email = Data['email']
            New_Password = Data['password']
            # Execute the query to update the user's password
            with connection.cursor() as cursor:
                 Select_Query = 'SELECT Employee_email FROM employee_complete_details '
                 cursor.execute(Select_Query)
                 Existing_Emails = [row['email'] for row in cursor.fetchall()]
                 if Email in Existing_Emails:
                   Update_Query = 'UPDATE employee_complete_details SET  Password = %s WHERE Employee_email = %s'
                   cursor.execute(Update_Query,(New_Password, Email))
                   print(Email,New_Password)
                   connection.commit()
                   Response_Data = {'status': 'success','message': ' email exist!!.. Password updated successfully'}
                   return jsonify(Response_Data)
                 else:
                     Response_Data={'status': 'failed and try again!', 'message': 'email not exist'}    
                     return jsonify(Response_Data)   





#................................................clockInOut...............................................
#checking clockin and clockout..................
from datetime import datetime, timedelta
from flask import jsonify, request

@app.route('/clock_in', methods=['POST'])
def Clock_In_Out():
    print("🔥 CLOCK IN HIT 🔥", request.get_json())

    data = request.get_json()

    # ================= BASIC DATA =================
    employee_id = data['employee_id']
    employee_name = data['employee_name']
    historic = data['historic']
    district = data['district']
    button_name = data['button_name']

    location = f"{historic} {district}"
    today_date = datetime.now().date()
    now_time = datetime.now().time()

    # ================= CHECK EXISTING ENTRY =================
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM Employee_Attendance_Data WHERE employee_id=%s AND Date=%s",
            (employee_id, today_date)
        )
        exist_data = cursor.fetchone()
        print(exist_data)

    # ========================================================
    # ======================= CLOCK IN =======================
    # ========================================================
    if button_name == 'clock_in':

        # ✅ FIRST CLOCK IN
        if not exist_data:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Employee_Attendance_Data
                    (employee_id, employee_name, clock_in_time, clock_in_location, clock_out_time, Date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (employee_id, employee_name, now_time, location, None, today_date))
                connection.commit()

            return jsonify({
                "status": "success",
                "message": "Clock-in successful",
                "current_time": now_time.strftime("%H:%M:%S")
            })

        # ❌ ALREADY CLOCKED IN
        clock_in_td = exist_data['clock_in_time']  # timedelta

        total_seconds = int(clock_in_td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        return jsonify({
            "status": "failed",
            "message": "Already clocked in today",
            "current_time": formatted_time
        })

    # ========================================================
    # ======================= CLOCK OUT ======================
    # ========================================================
    elif button_name == 'clock_out':

        if not exist_data :
            return jsonify({
                "status": "failed",
                "message": "No clock-in record found"
            })
        clock_out_td = exist_data['clock_out_time']
        if  exist_data['clock_out_time'] is not None:
            return jsonify({
                "status": "failed",
                "message": "Clock-out already recorded",
                
            })

        clock_in_td = exist_data['clock_in_time']
        clock_out_time = datetime.now().time()

        avg_working_td = (
            datetime.combine(datetime.today(), clock_out_time) -
            datetime.combine(datetime.today(), (datetime.min + clock_in_td).time())
        )

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE Employee_Attendance_Data
                SET clock_out_time=%s,
                    clock_out_location=%s,
                    Avg_working_hrs=%s
                WHERE employee_id=%s AND Date=%s
            """, (
                clock_out_time,
                location,
                avg_working_td,
                employee_id,
                today_date
            ))
            connection.commit()

        return jsonify({
            "status": "success",
            "message": "Clock-out successful",
            "working_hours": str(avg_working_td)
        })

    # ========================================================
    # ================= INVALID BUTTON =======================
    # ========================================================
    return jsonify({
        "status": "failed",
        "message": "Invalid button name"
    })




#.........................................AttendanceData................................................
   
#getting request and sending employee_attendance data based on request_type(all_data/between_dates..)
@app.route('/get_attendance_data', methods=['POST'])
def get_specific_attendance():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "failed",
                "message": "No JSON data received"
            }), 400

        employee_id = data.get('id')
        employee_name = data.get('username')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        request_type = data.get('request_type')

        if not employee_id or not request_type:
            return jsonify({
                "status": "failed",
                "message": "Missing required fields"
            }), 400

        with connection.cursor() as cursor:

            # =====================================================
            # 🔵 ALL DATA
            # =====================================================
            if request_type == 'all_data':

                cursor.execute("""
                    SELECT a.Date, a.clock_in_time, 
                           a.clock_out_time, a.Avg_working_hrs
                    FROM Employee_Attendance_Data a
                    LEFT JOIN ClockAdjustment ca
                      ON a.Employee_id = ca.Employee_id 
                     AND a.Date = ca.Selected_Date
                    WHERE a.Employee_id = %s
                      AND (ca.Employee_id IS NULL 
                           OR ca.Selected_Date IS NULL)
                    ORDER BY a.Date DESC
                """, (employee_id,))

                employee_info = cursor.fetchall()

            # =====================================================
            # 🔵 BETWEEN DATES
            # =====================================================
            elif request_type == 'between_dates':

                if not start_date or not end_date:
                    return jsonify({
                        "status": "failed",
                        "message": "Start and End dates required"
                    }), 400

                cursor.execute("""
                    SELECT Date, clock_in_time, 
                           clock_out_time, Avg_working_hrs
                    FROM Employee_Attendance_Data
                    WHERE Employee_id = %s
                      AND Date BETWEEN %s AND %s
                    ORDER BY Date DESC
                """, (employee_id, start_date, end_date))

                employee_info = cursor.fetchall()

            else:
                return jsonify({
                    "status": "failed",
                    "message": "Invalid request_type"
                }), 400

        # =====================================================
        # 🔵 FORMAT TIME FIELDS
        # =====================================================

        for row in employee_info:
            row['clock_in_time'] = str(row['clock_in_time'])
            row['clock_out_time'] = str(row['clock_out_time'])
            row['Avg_working_hrs'] = str(row['Avg_working_hrs'])
            row['Date'] = str(row['Date'])

        return jsonify({
            "status": "success",
            "Attendance_data": employee_info
        })

    except Exception as e:
        print("Exception in get_specific_attendance:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500





#not in use...................................................................................
#getting request and send all employee_names and leave balance data from leave_balance table based on employee_id
@app.route('/send_all_employee', methods=['POST'])
def Fetch_All_Employee():
    if request.method == 'POST':
      Data = request.get_json()
      print(Data)
      try:
        if Data:
          with connection.cursor() as cursor:
            #selecting all employee_names from main table
            Select_Query1 = 'SELECT Employee_Name FROM employee_complete_details '
            #selecting specific employee_leaves_data from leave_balance table...
            Select_Query2='SELECT Sick_Leave,Wedding_Leave,Maternity_Leave,Paternity_Leave,No_of_leaves,Taken_leaves,Pending_leaves FROM Leave_balance WHERE Employee_id=%s'
            cursor.execute(Select_Query1)              
            Employee_Names=cursor.fetchall()
            print("this is employee_names",Employee_Names)
            cursor.execute(Select_Query2,(Data['employee_id']))              
            Employee_Leave_Bal_Info=cursor.fetchall()
            print("employee leave balance data",Employee_Leave_Bal_Info)

            # If no leave balance record exists, auto-create a default one
            if not Employee_Leave_Bal_Info:
                cursor.execute(
                    'SELECT Employee_Name, Employee_email, Gender FROM employee_complete_details WHERE Employee_id=%s'
                )
                emp_row = cursor.fetchone()
                if emp_row:
                    sick    = float(emp_row.get('Sick_Leave') or 10)
                    wedding = float(emp_row.get('Wedding_Leave') or 0)
                    mat     = float(emp_row.get('Maternity_Leave') or 0)
                    pat     = float(emp_row.get('Paternity_Leave') or 0)
                    total   = sick + wedding + mat + pat
                    cursor.execute(
                        '''INSERT INTO Leave_balance
                           (Employee_id, Employee_Name, Employee_email, Gender,
                            Sick_Leave, Wedding_Leave, Maternity_Leave, Paternity_Leave,
                            No_of_leaves, Taken_leaves, Pending_leaves)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                        (Data['employee_id'], emp_row['Employee_Name'], emp_row['Employee_email'],
                         emp_row.get('Gender',''), sick, wedding, mat, pat, total, 0.0, total)
                    )
                    connection.commit()
                    # Re-fetch after insert
                    cursor.execute(Select_Query2,(Data['employee_id']))
                    Employee_Leave_Bal_Info=cursor.fetchall()
                    print("auto-created leave balance:", Employee_Leave_Bal_Info)

            response_data={'Employee_names': Employee_Names,'employee_leaves_data':Employee_Leave_Bal_Info}    
            return jsonify(response_data)
        else:
            print("employee not exist...")
            response_data = {'status': 'failed', 'message': 'user not exist....'}
            return jsonify(response_data)
      except Exception as e:
          print("exception occured in fetch_all_employee function and error is",e)
          return jsonify({'status':'failed','message':str(e)})





#........................................................AcceptLeaveRequest....................................................

@app.route('/accept/<request_id>/<person_name>', methods=['POST'])
def accept_request(request_id, person_name):

    print("Processing Accept for:", request_id)

    try:
        with connection.cursor() as cursor:

            # =====================================================
            # 1️ FETCH LEAVE REQUEST
            # =====================================================
            cursor.execute(
                "SELECT * FROM Leave_Request WHERE Request_id=%s",
                (request_id,)
            )
            leave_data = cursor.fetchone()

            if not leave_data:
                return jsonify({
                    "status": "failed",
                    "message": "Leave request not found"
                }), 404

            print("Current Status:", leave_data['Status'])

            #if leave_data['Status'].lower() == "accepted":
             #   return jsonify({
              #      "status": "failed",
               #     "message": "Leave already accepted"
                #}), 400


            # =====================================================
            # 2️⃣ UPDATE STATUS
            # =====================================================
            cursor.execute(
                "UPDATE Leave_Request SET Status=%s WHERE Request_id=%s",
                ("Accepted", request_id)
            )


            # Extract values
            employee_id = leave_data['Employee_id']
            employee_name = leave_data['Employee_Name']
            start_date = leave_data['Start_date']
            end_date = leave_data['End_date']
            no_of_days = float(leave_data['No_of_Days'])
            leave_type = leave_data['Leave_Type']
            reason = leave_data['Reason']
            team_lead = leave_data['Team_lead']
            team_lead_email = leave_data['Team_lead_email']
            manager_email = leave_data['Manager_email']
            add_employees = leave_data['Add_Employees']


            # =====================================================
            # 3️⃣ UPDATE LEAVE BALANCE
            # =====================================================

            allowed_leave_types = [
                "Sick_Leave",
                "Casual_Leave",
                "Earned_Leave",
                "Wedding_Leave",
                "Maternity_Leave",
                "Paternity_Leave"
            ]

            # Only update leave balance if leave_type is a valid known column
            if leave_type in allowed_leave_types:
                cursor.execute(f"""
                    SELECT Pending_leaves, Taken_leaves, {leave_type}
                    FROM Leave_balance
                    WHERE Employee_id=%s
                """, (employee_id,))

                balance = cursor.fetchone()

                if balance:
                    current_type_balance = float(balance[leave_type])
                    taken_leaves = float(balance['Taken_leaves'])
                    pending_leaves = float(balance['Pending_leaves'])

                    updated_type_balance = current_type_balance - no_of_days
                    updated_taken = taken_leaves + no_of_days
                    updated_pending = pending_leaves - no_of_days

                    cursor.execute(f"""
                        UPDATE Leave_balance
                        SET {leave_type}=%s,
                            Taken_leaves=%s,
                            Pending_leaves=%s
                        WHERE Employee_id=%s
                    """, (
                        updated_type_balance,
                        updated_taken,
                        updated_pending,
                        employee_id
                    ))
                else:
                    print(f"No leave balance record found for employee {employee_id}, skipping balance update")
            else:
                print(f"Leave type '{leave_type}' not in allowed list, skipping balance update")


            # =====================================================
            # 4️⃣ INSERT INTO HISTORY
            # =====================================================

            cursor.execute("""
                INSERT INTO Leave_history
                (Request_id, Employee_id, Employee_Name,
                 Start_date, End_date, No_of_Days,
                 Leave_Type, Add_Employees, Reason,
                 Status, Team_lead, Team_lead_email,
                 Manager_email, Approved_By_Whom)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                request_id,
                employee_id,
                employee_name,
                start_date,
                end_date,
                no_of_days,
                leave_type,
                add_employees,
                reason,
                "Accepted",
                team_lead,
                team_lead_email,
                manager_email,
                person_name
            ))


            # =====================================================
            # 5️⃣ DELETE FROM LEAVE_REQUEST
            # =====================================================

            cursor.execute(
                "DELETE FROM Leave_Request WHERE Request_id=%s",
                (request_id,)
            )


        # 🔵 Commit everything together
        connection.commit()


        # =====================================================
        # 6️⃣ SEND EMAIL (Safe block)
        # =====================================================

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT Employee_email
                    FROM employee_complete_details
                    WHERE Employee_id=%s
                """, (employee_id,))
                employee_row = cursor.fetchone()

            if employee_row:
                employee_email = employee_row['Employee_email']

                msg = Message(
                    'Leave Request Status',
                    sender='enerziff@gmail.com',
                    recipients=[employee_email]
                )

                msg.body = f"""
Hello {employee_name},

Your leave request from {start_date} to {end_date}
has been ACCEPTED.

Approved By: {person_name}

Thank You.
"""
                mail.send(msg)

        except Exception as e:
            print("Email error:", e)


        return jsonify({
            "status": "success",
            "message": f"Leave request accepted for {employee_name}"
        })


    except Exception as e:
        connection.rollback()
        print("EXCEPTION:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
             


#......................................................RejectLeaveRequest....................................................
#rejection mail...
@app.route('/reject/<request_id>/<person_name>', methods=['POST'])
def reject_request(request_id, person_name):

    print("Rejecting Request:", request_id)

    try:
        with connection.cursor() as cursor:

            # =====================================================
            # 1️⃣ FETCH LEAVE REQUEST
            # =====================================================
            cursor.execute(
                "SELECT * FROM Leave_Request WHERE Request_id=%s",
                (request_id,)
            )

            leave_data = cursor.fetchone()

            if not leave_data:
                return jsonify({
                    "status": "failed",
                    "message": "Leave request not found"
                }), 404

            if leave_data['Status'].lower() == "rejected":
                return jsonify({
                    "status": "failed",
                    "message": "Leave already rejected"
                }), 400


            # Extract values
            employee_id = leave_data['Employee_id']
            employee_name = leave_data['Employee_Name']
            start_date = leave_data['Start_date']
            end_date = leave_data['End_date']
            no_of_days = leave_data['No_of_Days']
            leave_type = leave_data['Leave_Type']
            reason = leave_data['Reason']
            team_lead = leave_data['Team_lead']
            team_lead_email = leave_data['Team_lead_email']
            manager_email = leave_data['Manager_email']
            add_employees = leave_data['Add_Employees']


            # =====================================================
            # 2️⃣ INSERT INTO LEAVE HISTORY (Rejected)
            # =====================================================

            cursor.execute("""
                INSERT INTO Leave_history
                (Request_id, Employee_id, Employee_Name,
                 Start_date, End_date, No_of_Days,
                 Leave_Type, Add_Employees, Reason,
                 Status, Team_lead, Team_lead_email,
                 Manager_email, Approved_By_Whom)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                request_id,
                employee_id,
                employee_name,
                start_date,
                end_date,
                no_of_days,
                leave_type,
                add_employees,
                reason,
                "Rejected",
                team_lead,
                team_lead_email,
                manager_email,
                person_name
            ))


            # =====================================================
            # 3️⃣ DELETE FROM LEAVE_REQUEST
            # =====================================================

            cursor.execute(
                "DELETE FROM Leave_Request WHERE Request_id=%s",
                (request_id,)
            )


        # Commit all DB operations
        connection.commit()


        # =====================================================
        # 4️⃣ SEND EMAIL (SAFE BLOCK)
        # =====================================================

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT Employee_email
                    FROM employee_complete_details
                    WHERE Employee_id=%s
                """, (employee_id,))
                employee_row = cursor.fetchone()

            if employee_row:
                employee_email = employee_row['Employee_email']

                msg = Message(
                    'Leave Request Status',
                    sender='enerziff@gmail.com',
                    recipients=[employee_email]
                )

                msg.body = f"""
Hello {employee_name},

Your leave request from {start_date} to {end_date}
has been REJECTED.

Rejected By: {person_name}

Reason: {reason}

Thank You.
"""
                mail.send(msg)

        except Exception as e:
            print("Email failed:", e)


        return jsonify({
            "status": "success",
            "message": f"Leave request rejected for {employee_name}"
        })


    except Exception as e:
        connection.rollback()
        print("EXCEPTION:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500





#generating random request_id..
def generate_id():
    return ''.join([str(random.randint(0, 9)) for _ in range(4)]) 



#...................................................LeaveRequest..................................................
#getting leave request data..........           
@app.route('/leave_request_data', methods=['POST'])
def leave():
        if request.method == 'POST':
            data = request.get_json()
            print(data)
            employee_id=data['id']
            employee_name=data['employee_name']
            Start_date=data['from_date']
            End_date=data['to_date']
            Leave_Type=data['leave_type']
            Reason=data['reason']
            # Add_employees=['Sudha',]         
            request_id=generate_id()
            Request_id=str(request_id)
            print(data)
            request_type=data['request_type']
            #extracting employee_names from add_employees...
            # employe_names=""
            # for i in range(len(Add_employees)):
            #      employe_names=Add_employees[i]+","+employe_names
            #      print(type(employe_names))
            with connection.cursor() as cursor: 
              current_date= datetime.now().strftime('%Y-%m-%d')
        # Current_Date=str(datetime.now().strftime('%Y-%m-%d'))
              Select_Query='select * FROM Employee_Attendance_Data WHERE Employee_id=%s AND Date=%s'
              cursor.execute(Select_Query,( employee_id,current_date))
              Exist_Data=cursor.fetchone()
              clock_in_time_str=""
              print("upto this1")
              try:
               clock_in_time_str=str(Exist_Data['clock_in_time'])
        #   clock_in_time_str = datetime.strptime(Exist_Data['clock_in_time'], "%H:%M:%S")
               print("upto this2")
              except:
               clock_in_time_str=""
            with connection.cursor() as cursor:                       
                    select_employe = "SELECT Team_lead_email,Manager_email,Team_lead ,Manager_name FROM  employee_complete_details  WHERE Employee_id = %s "
                    cursor.execute(select_employe , (employee_id,))  
                    employe_row = cursor.fetchone()
                    print("employee data",employe_row)
                    
                    if not employe_row:
                        return jsonify({
                            "status": "error",
                            "message": "Employee not found in employee_complete_details"
                        }), 400
                    Team_lead_email=employe_row['Team_lead_email']
                    Manager_email=employe_row['Manager_email']
                    Team_lead=employe_row['Team_lead']
                    Manager_name=employe_row['Manager_name']
                    print("team lead emails",Team_lead_email,Manager_email) 
                    End_date = datetime.strptime(End_date, '%Y-%m-%d')
                    Start_date = datetime.strptime(Start_date, '%Y-%m-%d')
                    No_of_Days=(End_date - Start_date).days
                    current_date= datetime.now().strftime('%Y-%m-%d')
                    applied_on=datetime.now().strftime('%Y-%m-%d')
            if request_type=="insert":
                  print("this is insert function",Start_date,End_date)
                  print("applied_on...",applied_on)
                  with connection.cursor() as cursor:
                    print("up to this1")
                    insert_into_leave_request= "INSERT INTO Leave_Request (Request_id,Employee_id,Employee_Name,Start_date,End_date,No_of_Days,Leave_Type,Add_Employees,Reason,Status,Team_lead ,Team_lead_email,Manager_email,Applied_on) VALUES (%s,%s,%s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(insert_into_leave_request, (Request_id,employee_id,employee_name,Start_date,End_date,No_of_Days,Leave_Type,'NONE',Reason,"Waiting",Team_lead,Team_lead_email,Manager_email,applied_on))
                    print("up to this2")

                    connection.commit()
                    print("upto this 3")       
                    # response={'status':"success",'message':"leave_request data inserted successfully..."}
                    # return jsonify(response)
                    html = render_template_string(
                                                  """
                                                  <p>Dear {{ team_lead }},</p>
                                                  <p>I hope this message finds you well. I am writing to formally request leave for the following dates:</p>
                                                  <p>Start Date: <strong>{{ start_date }}</strong></p>
                                                  <p>End Date: <strong>{{ end_date }}</strong></p>
                                                  <p>Total Number of Days: <strong>{{ total_days }}</strong></p>
                                                  <p>Reason for Leave: <strong>{{ reason }}</strong></p>
                                                  <p>I understand the importance of my role and the impact of my absence on the team. Rest assured, I have planned my tasks accordingly to minimize any disruption during my absence.</p>
                                                  <p>I would like to inquire if there are any supporting documents or forms that I need to submit along with this leave request. Please let me know if there is anything else required from my end.</p>
                                                  <p><strong>Your support and understanding are invaluable to me. Thank you for your time and consideration.</strong></p>
                                                  <p>Best regards,</p>
                                                  <p>{{ employee_name }}</p>                                                  
                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name, _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(request_id),
                                                 person_name=Team_lead,
                                                 team_lead=Team_lead,
                                                 start_date=Start_date,
                                                 end_date=End_date,
                                                 total_days=No_of_Days,
                                                 reason=Reason,
                                                 employee_name=employee_name

                                                 
                                                 )
                    msg_team_lead = Message(
                                    'Leave Request',
                    sender='enerziff@gmail.com',
                    recipients=[Team_lead_email]
                    )
                    msg_team_lead.body = "You have got a leave request from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                    msg_team_lead.html = html
                    try:
                        mail.send(msg_team_lead)
                    except Exception as e:
                        print("Email error (non-fatal):", e)
                    
          
                    # Send email to manager
                    html = render_template_string(
                                                  """
                                                  <p>Dear {{ person_name }},</p>
                                                  <p>I hope this message finds you well. I am writing to formally request leave for the following dates:</p>
                                                  <p>Start Date: <strong>{{ start_date }}</strong></p>
                                                  <p>End Date: <strong>{{ end_date }}</strong></p>
                                                  <p>Total Number of Days: <strong>{{ total_days }}</strong></p>
                                                  <p>Reason for Leave: <strong>{{ reason }}</strong></p>
                                                  <p>I understand the importance of my role and the impact of my absence on the team. Rest assured, I have planned my tasks accordingly to minimize any disruption during my absence.</p>
                                                  <p>I would like to inquire if there are any supporting documents or forms that I need to submit along with this leave request. Please let me know if there is anything else required from my end.</p>
                                                  <p><strong>Your support and understanding are invaluable to me. Thank you for your time and consideration.</p>
                                                  <p>Best regards,</strong></p>
                                                  <p>{{ employee_name }}</p>
                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(request_id),
                                                 person_name=Manager_name,
                                                 start_date=Start_date,
                                                 end_date=End_date,
                                                 total_days=No_of_Days,
                                                 reason=Reason,
                                                 employee_name=employee_name

                                                 
                                                 )
                    msg_manager = Message(
                    'Leave Request',
                    sender='enerziff@gmail.com',
                    recipients=[Manager_email]
                    )
                    msg_manager.body = "You have got a leave request from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                    msg_manager.html = html
                    try:
                        mail.send(msg_manager)
                        print("mail sent to manager")
                    except Exception as e:
                        print("Email error (non-fatal):", e)
                    current_date= datetime.now().strftime('%Y-%m-%d')
                  response={'status':"success",'From_date':Start_date,'To_date':End_date,'Applied_on':current_date}
                  return jsonify(response)


            elif request_type == "update":
                        print("this is update function", Start_date, End_date)
                        with connection.cursor() as cursor:
                          sql='SELECT Request_id FROM Leave_Request WHERE Employee_id=%s'
                          cursor.execute(sql,(employee_id))
                          query=cursor.fetchone()
                          request_id=query['Request_id']
                          update_sql = "UPDATE Leave_Request SET  Start_date=%s, End_date=%s, No_of_Days=%s, Leave_Type=%s, Add_Employees=%s, Reason=%s  WHERE Employee_id=%s"
                          cursor.execute(update_sql, ( Start_date, End_date, No_of_Days, Leave_Type,'NONE ', Reason, employee_id))
                          connection.commit()
                          print("updated the leave request data")
                        #   response = {'status': "success", 'message': "leave_request data updated successfully..."}
                        #   return jsonify(response)
                          html = render_template_string(
                                                  """
                                                  <p>Your request_id: <strong>{{ Request_id }}</strong></p>
                                                  <p>Team Lead: <strong>{{ person_name }}</strong></p>
                                                 
                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name, _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(request_id),
                                                 person_name=Team_lead,
                                                 team_lead=Team_lead,
                                                 start_date=Start_date,
                                                 end_date=End_date,
                                                 total_days=No_of_Days,
                                                 reason=Reason,
                                                 employee_name=employee_name
                                                 
                                                 )
                          msg_team_lead = Message(
                                        'Leave Request',
                          sender='enerziff@gmail.com',
                          recipients=[Team_lead_email]
                           )
                          msg_team_lead.body = "You have got a leave request from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                          msg_team_lead.html = html
                          try:
                              mail.send(msg_team_lead)
                              print("mail sent to team_lead")
                          except Exception as e:
                              print("WFH update team lead email error:", e)

                    # Send email to manager
                          html = render_template_string(
                                                  """
                                                  <p>Your request_id: <strong>{{ Request_id }}</strong></p>
                                                  <p>Manager: <strong>{{person_name}}</strong></p>
                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(request_id),
                                                 person_name=Manager_name,
                                                 
                                                 )
                          msg_manager = Message(
                            'Leave Request',
                            sender='enerziff@gmail.com',
                            recipients=[Manager_email]
                            )
                          msg_manager.body = "You have got a leave request from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                          msg_manager.html = html
                          mail.send(msg_manager)
                          print("mail sent to manager")

                        response={'status':"success",'From_date':Start_date,'To_date':End_date,'Applied_on':applied_on}
                        return jsonify(response)



            elif request_type=='Partial':
              leave_typ="Sick_Leave"
              reason=Leave_Type + "  " +Reason
              No_of_Day=float(0.5)
              No_Of_Days=float(No_of_Day)
              print("data type",type(No_Of_Days))
              print("Number_of_days:",No_Of_Days)
              # print("this is partial function",Start_date,End_date)
              print("applied_on...",applied_on)
              Start_date=datetime.now().strftime('%Y-%m-%d')
              print("current_date is..",Start_date)
              with connection.cursor() as cursor:
                    print("up to this1")
                    insert_into_leave_request= "INSERT INTO Leave_Request (Request_id,Employee_id,Employee_Name,Start_date,End_date,No_of_Days,Leave_Type,Add_Employees,Reason,Status,Team_lead ,Team_lead_email,Manager_email,Applied_on) VALUES (%s,%s,%s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(insert_into_leave_request, (Request_id,employee_id,employee_name,Start_date,End_date,No_Of_Days,leave_typ,'NONE',reason,"Waiting",Team_lead,Team_lead_email,Manager_email,applied_on))
                    print("up to this2")

                    connection.commit()
                    print("upto this 3")       
                    # response={'status':"success",'message':"leave_request data inserted successfully..."}
                    # return jsonify(response)
                    html = render_template_string(
                                                   """
                                                  <p>Dear {{ person_name }},</p>

                                                  <p><strong>Subject:</strong> Half-Day Leave Application</p>

                                                  <p>I hope this message finds you well. I regret to inform you that due to {{ Reason }}, I will be unable to report to work on time on {{ Leave_Date }}.</p>

                                                  <p>I understand the importance of my responsibilities and the impact of my absence on the team. Therefore, I will be taking {{ leave_type }} and will ensure to complete as much work as possible before my leave.</p>

                                                  <p>In case of any emergencies or inquiries, I can be reached on my phone. I trust that the team will manage efficiently during my absence.</p>

                                                  <p>I would like to inquire if there are any supporting documents or forms required to accompany this leave request. Please let me know if there is anything else needed from my end.</p>

                                                  <p>Your support and understanding are invaluable to me. Thank you for your time and consideration.</p>

                                                  <p><strong>Best regards,</strong></p>
                                                  <p>{{ employee_name }}</p>
                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                  
                                                 Request_id=str(request_id),
                                                 person_name=Team_lead,
                                                 leave_type=leave_typ,
                                                 Reason=Reason,
                                                 Leave_Date=Start_date,
                                                 Leave_Type=Leave_Type,
                                                 employee_name=employee_name,
                                                 )
                    msg_team_lead = Message(
                                    'Leave Request',
                    sender='enerziff@gmail.com',
                    recipients=[Team_lead_email]
                    )
                    msg_team_lead.body = "You have got a leave request from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                    msg_team_lead.html = html
                    mail.send(msg_team_lead)
                    print("mail sent to team_lead")
          


                    # Send email to manager
                    html = render_template_string(
                                                  """
                                                  <p>Dear {{ person_name }},</p>

                                                  <p><strong>Subject:</strong> Half-Day Leave Application</p>

                                                  <p>I hope this message finds you well. I regret to inform you that due to {{ Reason }}, I will be unable to report to work on time on {{ Leave_Date }}.</p>

                                                  <p>I understand the importance of my responsibilities and the impact of my absence on the team. Therefore, I will be taking {{ leave_type }} and will ensure to complete as much work as possible before my leave.</p>

                                                  <p>In case of any emergencies or inquiries, I can be reached on my phone. I trust that the team will manage efficiently during my absence.</p>

                                                  <p>I would like to inquire if there are any supporting documents or forms required to accompany this leave request. Please let me know if there is anything else needed from my end.</p>

                                                  <p>Your support and understanding are invaluable to me. Thank you for your time and consideration.</p>

                                                  <p><strong>Best regards,</strong></p>
                                                  <p>{{ employee_name }}</p>
                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(request_id),
                                                 person_name=Manager_name,
                                                 leave_type=leave_typ,
                                                 Reason=Reason,
                                                 Leave_Date=Start_date,
                                                 Leave_Type=Leave_Type,
                                                 employee_name=employee_name,
                                                 )
                    msg_manager = Message(
                    'Leave Request',
                    sender='enerziff@gmail.com',
                    recipients=[Manager_email]
                    )
                    msg_manager.body = "You have got a leave request from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                    msg_manager.html = html
                    mail.send(msg_manager)
                    print("mail sent to manager")
                    current_date= datetime.now().strftime('%Y-%m-%d')
                    response={'status':"success",'From_date':Start_date,'To_date':End_date,'Applied_on':current_date,'clock_in_time':clock_in_time_str,}
                    return jsonify(response)

            else:
              print("request type is invalid.....")



#.............................................Insert StatusUpdateData...............................................
              
#getting daily status update data and insert into daily status update table
@app.route('/status_update_data', methods=['POST'])
def Insert_Into_Status():
        if request.method == 'POST':
            Data = request.get_json()
            print(Data)
            Employee_Email=Data['email']
            Completed_Task=Data['completed']
            Issues=Data['issues']
            Feature_Targets=Data['upcoming']
            Status_Update=Data['statusUpdate']
            Employee_Name=Data['employeename']
            Employee_Id=Data['employeeid'] 
            Date1=Data['date']
            Date_Formatted = datetime.strptime(Date1, '%Y-%m-%d') 
            print("this is date_formated",Date_Formatted) 
            # current_date_formatted = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.strptime(datetime.now().strftime("%H:%M:%S"), "%H:%M:%S")
        with connection.cursor() as cursor:
           print("employee_name and email:",Employee_Name,Employee_Email)
           #INSERT DATA INTO DAILY STATUS UPDATE DATA TABLE...
           Select_Query = "INSERT INTO Daily_Status_Update (Employee_id, Employee_Name, Employee_Email,Date,Time,Status_Update,Issues,Completed_Task,Feature_Targets) VALUES (%s, %s, %s, %s, %s,%s,%s,%s,%s)"
           cursor.execute(Select_Query, (Employee_Id, Employee_Name,  Employee_Email,Date_Formatted ,current_time,Status_Update,Issues, Completed_Task,Feature_Targets))
           connection.commit()
           #SENDING RESPONSE..........
           Response_Data = {'status': 'success', 'message': 'employee registred successfully'}
        return jsonify(Response_Data)   
    



#...................................................Update Status.............................................

#updating status update data table..............
@app.route('/specific_status_update', methods=['POST'])
def Update_specific_status():
        if request.method == 'POST':
            Data = request.get_json()
            print("data for updating the status_table",Data)
            # Employee_Email=data['email']
            Completed_Task=Data['completed']
            Issues=Data['issues']
            Feature_Targets=Data['targets']
            Status_Update=Data['status']
            # Employee_Name=data['employeename']
            Employee_Id=Data['id']
            Date=Data['date']    
        with connection.cursor() as cursor: 
            Current_Date = datetime.strptime(Date, '%Y-%m-%d') 
            #updating the daily _status_data table....  
            Select_Query = "UPDATE Daily_Status_Update SET Status_Update=%s,Issues=%s,Completed_Task=%s,Feature_Targets=%s WHERE Employee_id=%s AND Date=%s"
            cursor.execute(Select_Query, (Status_Update,Issues,Completed_Task,Feature_Targets,Employee_Id,Current_Date))
            connection.commit()
            #sending response......
            Response_Data = {'status': 'success', 'message': 'employee registred successfully'}
        return jsonify(Response_Data)   





#............................................Fetch StatusData............................................

# sending emmployee daily status update details based on employee_name ,employee_id and specific date...
from datetime import datetime

@app.route('/get_status_update_data', methods=['POST'])
def Fetch_Specific_Status():
    if request.method == 'POST':
        Data = request.get_json()
        print(Data)

        Employee_Id = Data.get('employeeid')
        Request_Type = Data.get('request_type')
        Start_Date = Data.get('start_date')
        End_Date = Data.get('end_date')

        # ✅ Always validate start date
        if not Start_Date:
            return jsonify({"status": "failed", "message": "Start date is required"}), 400

        Start_date_Formatted = datetime.strptime(Start_Date, '%Y-%m-%d')

        # 🔹 SINGLE DATE
        if Request_Type == 'single_date':
            with connection.cursor() as cursor:
                Select_Query = "SELECT * FROM Daily_Status_Update WHERE Employee_id = %s AND Date = %s"
                cursor.execute(Select_Query, (Employee_Id, Start_date_Formatted))
                Employe_Row = cursor.fetchone()

                if Employe_Row:
                    Employe_Row['Time'] = str(Employe_Row['Time'])

                return jsonify({"status": "success", "status_update": Employe_Row})

        # 🔹 BETWEEN DATES
        elif Request_Type == 'in_between_dates':

            # ✅ Validate End_Date here ONLY
            if not End_Date:
                return jsonify({"status": "failed", "message": "End date is required"}), 400

            End_Date_Formatted = datetime.strptime(End_Date, '%Y-%m-%d')

            with connection.cursor() as cursor:
                Select_Query = '''
                SELECT * FROM Daily_Status_Update 
                WHERE Employee_id = %s AND Date BETWEEN %s AND %s
                '''
                cursor.execute(Select_Query, (Employee_Id, Start_date_Formatted, End_Date_Formatted))
                Daily_Status_Info = cursor.fetchall()

                for row in Daily_Status_Info:
                    row['Time'] = str(row['Time'])

                return jsonify({
                    'status': 'success',
                    'message': 'Daily_status_info_in_between_dates',
                    'request_data': Daily_Status_Info
                })

        else:
            return jsonify({'status': 'failed', 'message': 'invalid request_type'})
        




#................................................Fetch LeaveData..............................................
            
#getting request (id and name) and sending the specific data based on the request from leave_request_table  
@app.route('/get_leave', methods=['POST'])
def Fetch_Specific_Leave():
        if request.method == 'POST':
            Data = request.get_json()
            print(Data)
            Employee_Name=Data['username']
            Employee_Id=Data['id ']          
        with connection.cursor() as cursor:  
            #selecting leave_request_data based on employee id and name...                     
            Select_Query = "SELECT * FROM Leave_Request WHERE Employee_Name = %s AND Employee_id = %s "
            cursor.execute(Select_Query , (Employee_Name, Employee_Id,))  
            Employe_Row = cursor.fetchone()
            if Employe_Row:
                print("employee data",Employe_Row)  
                Start_Date=Employe_Row['Start_date']
                Start_Date_Formatted = datetime.strptime(str(Start_Date),'%Y-%m-%d').date() 
                print(Start_Date_Formatted) 
                End_Date=Employe_Row['End_date']
                End_Date_Formatted = datetime.strptime(str(End_Date),'%Y-%m-%d').date()
                #sending response start and end dates along with leave_request_data......
                Response_Data={'status':"success",'from_date':Start_Date_Formatted,'To_date': End_Date_Formatted,'Leave_type':Employe_Row['Leave_Type'],'Add_Employees':Employe_Row['Add_Employees'],'reason':Employe_Row['Reason']}
                print("data sent successfully")
                return jsonify(Response_Data)
            else:
                 Response_Data={'status':'failed','message':'employee_id or employee_name should not matching'}
                 return jsonify(Response_Data)
            





#.......................................................DOB..........................................................
            
#getting request and sending employee_name and DOB based on  between dates.... and sending data from leave_history....
@app.route('/date_of_birth', methods=['POST'])
def Fetch_Specific_Dates_Info():
    if request.method == 'POST':
        Data = request.get_json()
        print(Data)
        with connection.cursor() as cursor:   
            Date = datetime.now().date()
            Date_Formatted= datetime.now().strftime('%Y-%m-%d')
            No_Of_Days=30
            Month_Added_Date = Date + timedelta(days=No_Of_Days)
            New_Date_str = Month_Added_Date.strftime('%Y-%m-%d')
            # Date=Date+no_of_days
            print("today date is:",New_Date_str)
            #selecting specific info based on present and after one month dates....                 
            Select_Query="SELECT Date_of_birth,Employee_Name FROM employee_complete_details WHERE Date BETWEEN %s AND %s"
            cursor.execute(Select_Query,(Date_Formatted,New_Date_str))  
            Required_Row = cursor.fetchall()
            print("data is:",Required_Row) 
            Select_Query="SELECT Employee_Name , Start_date, End_date , No_of_Days,DATE_FORMAT(Start_date, '%Y-%m-%d') AS formatted_date FROM Leave_history WHERE Start_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 1 MONTH)"
            cursor.execute(Select_Query)
            Required_Info=cursor.fetchall()
            print("info is:",Required_Info)
            #selecting leave request information.......
            Select_Query='SELECT * FROM Leave_Request'
            cursor.execute(Select_Query)
            Leave_Request_Data=cursor.fetchall()
            #selecting all employee count..... from main table
            Select_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
            cursor.execute(Select_Query)
            Employee_Count=cursor.fetchall()
            #selecting all employee count..... from attendance table
            Date= datetime.now().strftime('%Y-%m-%d')
            Select_Query='SELECT COUNT(Employee_id) FROM Employee_Attendance_Data WHERE DATE=%s'
            cursor.execute(Select_Query,Date)
            Clock_In_Count=cursor.fetchall()
            #selecting all employee data..... from attendance table
            Select_Query='SELECT * FROM Employee_Attendance_Data WHERE DATE=%s'
            cursor.execute(Select_Query,Date)
            Clock_In_Info=cursor.fetchall() 
            for i in range(len(Clock_In_Info)):
                            clock_in_time=str(Clock_In_Info[i]['clock_in_time'])
                            clock_out_time=str(Clock_In_Info[0]['clock_out_time'])
                            Avg_working_hrs=str(Clock_In_Info[0]['Avg_working_hrs'])
                            Clock_In_Info[i]['clock_in_time']=clock_in_time
                            Clock_In_Info[i]['clock_out_time']=clock_out_time
                            Clock_In_Info[i]['Avg_working_hrs']=Avg_working_hrs
            #selecting all data..... from Announcement table
            Select_Query='SELECT * FROM Announcement'
            cursor.execute(Select_Query)
            Announcement_Info=cursor.fetchall()
            #selecting all data..... from Holiday table
            Select_Query='SELECT * FROM Holiday'
            cursor.execute(Select_Query)
            Holiday_Info=cursor.fetchall()
            #sending response DOB and employenames,Leave_data,leave_request_data,total_no_of_employees,tdy_clk_in_count,clock_in_info,Announcement_data,Holiday_data
            Response_Data={'status':'success','DOB and employenames':Required_Row,'Leave_data':Required_Info,'leave_request_data':Leave_Request_Data,
                           'total_no_of_employees':Employee_Count,'tdy_clk_in_count':Clock_In_Count,'clock_in_info': Clock_In_Info,
                           'Announcement_data':Announcement_Info,'Holiday_data':Holiday_Info}
            print("requested data sent successfully:")
            return jsonify(Response_Data) 
        


#....................................................Insert Holiday..................................................
        
#INSERTING DATA INTO HOLIDAY TABLE..................
@app.route('/holiday', methods=['POST'])
def Insert_Holiday():
    if request.method == 'POST':
        Data = request.get_json()
        print(Data)
        Holiday_Date=Data['date']
        Fest_Name=Data['festival_name']
        print("data is",Data)
        Date= datetime.strptime(Holiday_Date,'%Y-%m-%d') 
        print("date is",Date)
        try:
          with connection.cursor() as cursor:
            Select_Query='INSERT INTO Holiday(Festival_name,Holiday_date) VALUES(%s,%s)'
            cursor.execute(Select_Query,(Fest_Name,Date))
            connection.commit()
            Response_Data={'status':'success',"message":'data inserted into holiday table successfully..'}
            return jsonify(Response_Data) 
        except Exception as e:
            print("exception occerd in Insert_Holiday function n error is ",e)




#....................................................Insert Announcement..............................................
            
#INSERTING DATA INTO Annoouncement TABLE..................
@app.route('/announcement', methods=['POST'])
def Insert_Announcement():
     if request.method=='POST':
          Data=request.get_json()
          print("the data is..... ",Data)
          Employee_Id=Data['Employee_id']
          print("Checking Employee_Id:", Employee_Id)
          Employee_Name=Data['Employee_Name']
          Announcement=Data['Announcement']
        #inserting_date=data['inserting_date']
          Announcement_Date=Data['Announcement_date']
          inserting_date=datetime.now().strftime('%Y-%m-%d')
        
          with connection.cursor() as cursor:
            Insert_Query='INSERT INTO Announcement (Employee_id,Employee_Name,Announcement,Inserting_date, Announcement_date) VALUES(%s,%s,%s,%s,%s)'
            cursor.execute(Insert_Query,(Employee_Id,Employee_Name,Announcement,inserting_date,Announcement_Date))
            connection.commit()
            print("hi mamatha executing this code")
            Response_Data={'status':'success',"message":'Announcement data inserted into Announcement_table successfully..'}
          with connection.cursor() as cursor:
            Current_Date = datetime.now().date()
            Current_Formate_Date= datetime.now().strftime('%Y-%m-%d')
            No_Of_Days=30
            New_Date_Str = Current_Date + timedelta(No_Of_Days)
            New_Date= New_Date_Str.strftime('%Y-%m-%d')
            print("Current Formatted Date:", Current_Formate_Date)
            print("New Date:", New_Date)
            Announcement_Query='SELECT Employee_Name,Announcement,Announcement_date FROM Announcement WHERE Announcement_date BETWEEN  %s AND %s'
            cursor.execute(Announcement_Query,(Current_Formate_Date, New_Date))
            Announcement_Info=cursor.fetchall()
            print("this is dateeeeeee",Announcement_Info)
            Response_Data={'status':'success',"message":'Announcement data inserted into Announcement_table successfully..',"Announcement_Info":Announcement_Info}
            return jsonify(Response_Data)


@app.route('/delete_announcement', methods=['POST'])
def delete_announcement():
  Data=request.get_json()
  print("the data is..... ",Data)
  Employee_Id=Data['Employee_id']
  user_type=Data['user_type']
  Announcement=Data['Announcement']
  Announcement_Date=Data['Announcement_date']
  if user_type=="Employee":
    with connection.cursor() as cursor:
      delete_Query = 'DELETE FROM Announcement WHERE Employee_id = %s AND Announcement_Date = %s'
      cursor.execute(delete_Query, (Employee_Id, Announcement_Date))
      connection.commit() 
      print("this is deleting fun() of if block")
      Response_Data={'status':'success',"message":'Announcement data inserted into Announcement_table successfully..'}
  else:
    with connection.cursor() as cursor:
      delete_Query = 'DELETE FROM Announcement WHERE Announcement_Date = %s'
      cursor.execute(delete_Query, (Announcement_Date))
      connection.commit() 
      print("this is deleting fun() of else block")
      Response_Data={'status':'success',"message":'Announcement data inserted into Announcement_table successfully..'}

  with connection.cursor() as cursor:
    Current_Date = datetime.now().date()
    Current_Formate_Date= datetime.now().strftime('%Y-%m-%d')
    No_Of_Days=30
    New_Date_Str = Current_Date + timedelta(No_Of_Days)
    New_Date= New_Date_Str.strftime('%Y-%m-%d')
    print("Current Formatted Date:", Current_Formate_Date)
    print("New Date:", New_Date)
    Announcement_Query='SELECT Employee_Name,Announcement,Announcement_date FROM Announcement WHERE Announcement_date BETWEEN  %s AND %s'
    cursor.execute(Announcement_Query,(Current_Formate_Date, New_Date))
    Announcement_Info=cursor.fetchall()
    print("this is dateeeeeees",Announcement_Info)
    Response_Data={'status':'success',"message":'Announcement data inserted into Announcement_table successfully..',"Announcement_Info":Announcement_Info}
    return jsonify(Response_Data)





@app.route('/Announcement_Info', methods=['POST'])
def Announcement_Info():
    if request.method=='POST':
       Data=request.get_json()
       Current_Date = datetime.now().date()
       Current_Formate_Date= datetime.now().strftime('%Y-%m-%d')
       No_Of_Days=30
       New_Date_Str = Current_Date + timedelta(No_Of_Days)
       New_Date= New_Date_Str.strftime('%Y-%m-%d')
       with connection.cursor() as cursor:
            Announcement_Query='SELECT Employee_Name,Announcement,Announcement_date FROM Announcement WHERE Announcement_date BETWEEN  %s AND %s'
            cursor.execute(Announcement_Query,(Current_Formate_Date, New_Date))
            Announcement_Info=cursor.fetchall()
            print("this is announcement date_info",Announcement_Info)
            Response_Data={'status':'success',"Announcement_Info":Announcement_Info}
       return jsonify(Response_Data)
    else:
           Announcement_Info=""
           Response_Data={'status':'failed',"Announcement_Info":Announcement_Info}
           return jsonify(Response_Data)



#........................................................StatusData................................................
          
#daily_status_update_details_basedon_specific_dates...............
@app.route('/status_data', methods=['POST'])
def status_details_specific():
     if request.method=='POST':
          Data=request.get_json()
          Start_Date=Data['start_date']
          End_Date=Data['end_date']
          print(Data)
          #converting dates into formatted dates......
          Start_Date_Formatted= datetime.strptime(Start_Date, '%Y-%m-%d') 
          End_Date_Formatted= datetime.strptime(End_Date, '%Y-%m-%d')
          with connection.cursor() as cursor:
               Select_Query='SELECT * FROM Daily_Status_Update WHERE Date BETWEEN %s and %s '
               cursor.execute(Select_Query,(Start_Date_Formatted,End_Date_Formatted))
               Daily_Status_Info=cursor.fetchall()
               Response_Data={'status':'success',"daily_status_data":Daily_Status_Info}
               return jsonify(Response_Data)





#............................................AttendanceData...............................................
#sending employee_attendance_details_basedon_specific_dates.....
@app.route('/attendance_data', methods=['POST'])
def Fetch_Attendance_Specific_Dates():
     if request.method=='POST':
          Data=request.get_json()
          Start_Date=Data['start_date']
          End_Date=Data['end_date']
          Start_Date= datetime.strptime(Start_Date, '%Y-%m-%d') 
          End_Date= datetime.strptime(End_Date, '%Y-%m-%d')
          with connection.cursor() as cursor:
               Select_Query='SELECT * FROM Employee_Attendance_Data WHERE Date BETWEEN %s and %s '
               cursor.execute(Select_Query,(Start_Date,End_Date))
               Attendance_Info=cursor.fetchall()
               for i in range(len(Attendance_Info)):
                            clock_in_time=str(Attendance_Info[i]['clock_in_time'])
                            clock_out_time=str(Attendance_Info[0]['clock_out_time'])
                            Avg_working_hrs=str(Attendance_Info[0]['Avg_working_hrs'])
                            Attendance_Info[i]['clock_in_time']=clock_in_time
                            Attendance_Info[i]['clock_out_time']=clock_out_time
                            Attendance_Info[i]['Avg_working_hrs']=Avg_working_hrs              
               Response_Data={'status':'success',"Attendance_Info":Attendance_Info}
               return jsonify(Response_Data)





#...............................................Insert LeaveBalance.....................................................
          
#insering data into leave_balance after calculating the all leaves......
@app.route('/leave_balance', methods=['POST'])
def Insert_Leave_Balance():
     if request.method=='POST':
       try:
          Data=request.get_json()
          print("data is...",Data)
          Employee_Id=Data['employee_id']
          Employee_Name=Data['employee_name']
          Sick_Leave=Data['sick_leave']
          Wedding_Leave=Data['wedding_leave']
          Maternity_Leave=Data['maternity_leave']
          Paternity_Leave=Data['paternity_leave']
          #calculating leaves..........
          No_Of_Days=3.0
          Taken_Leaves=0.0
          Pending_Leaves=0.0
          Sick_Leave=float(Sick_Leave)
          Wedding_Leave=float(Wedding_Leave)
          Maternity_Leave=float(Maternity_Leave)
          Paternity_Leave=float(Paternity_Leave)
          print("the type...",type(Sick_Leave))
          No_of_Leaves=float(Sick_Leave)+float(Wedding_Leave)+float(Maternity_Leave)+float(Paternity_Leave)
          print("sick_leave_type",type(Sick_Leave))
          Taken_Leaves=float(Taken_Leaves) + No_Of_Days
          Pending_Leaves=float(Pending_Leaves) - No_Of_Days
          print("type is",type(Pending_Leaves))
          No_of_Leaves=str(No_of_Leaves)
          Taken_Leaves=str(Taken_Leaves)
          Pending_Leaves=str(Pending_Leaves)
          with connection.cursor() as cursor:
            Select_Query='SELECT Employee_email,Gender FROM employee_complete_details WHERE Employee_id =%s'
            cursor.execute(Select_Query,( Employee_Id))
            Emp_Info=cursor.fetchone()
            employee_email=Emp_Info['Employee_email']
            gender=Emp_Info['Gender']
            Insert_Query='INSERT INTO Leave_balance(Employee_id,Employee_Name,Employee_email,Gender, Sick_Leave, Wedding_Leave, Maternity_Leave,Paternity_Leave,No_of_leaves,Taken_leaves, Pending_leaves) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            cursor.execute(Insert_Query,(Employee_Id,Employee_Name,employee_email,gender,Sick_Leave,Wedding_Leave,Maternity_Leave,Paternity_Leave,No_of_Leaves,Taken_Leaves,Pending_Leaves))
            connection.commit()
            Response_Data={'status':'success',"message":'leave data inserted into leave_balance_table successfully..'}
            return jsonify(Response_Data)
       except Exception as e :
          print("exception occerd in Insert_Leave_Balance function and error is:",e)





#..............................................Fetch EmpHistory...........................................
          
#getting user_id as request and sending leave_history data of a specific user......
@app.route('/accepted_leave_history', methods=['POST'])
def Fetch_Emp_History():
    if request.method == 'POST':
        Data = request.get_json()
        print(Data)       
        Employee_Id=Data['employee_id']
        Request_Type=Data['request_type']
        try:          
         if Request_Type=='accept':       
            with connection.cursor() as cursor: 
                Select_Query='SELECT * FROM Leave_history WHERE Employee_id=%s AND Status=%s'
                cursor.execute(Select_Query,(Employee_Id,'Accepted'))
                Emp_Info=cursor.fetchall()
                print("this is for accept function",Emp_Info)
                if Emp_Info:
                   Response_Data={'status':'Success','Employee_Leave_history':Emp_Info}
                   return jsonify(Response_Data)
                else:
                    Response_Data={'status':'failed','message':'requested_user_id not exist in table..'}
                    return jsonify(Response_Data)
         elif Request_Type=='pending':
             with connection.cursor() as cursor: 
                Select_Query='SELECT * FROM Leave_Request WHERE Employee_id=%s'
                cursor.execute(Select_Query,(Employee_Id))
                Emp_Info=cursor.fetchall()
                if Emp_Info:
                   Response_Data={'status':'Success','Employee_Leave_history':Emp_Info}
                   return jsonify(Response_Data)
                else:
                    Response_Data={'status':'failed','message':'requested_user_id not exist in table..'}
                    return jsonify(Response_Data)
         elif Request_Type=='reject':
             with connection.cursor() as cursor: 
                Select_Query='SELECT * FROM Leave_history WHERE Employee_id=%s AND Status=%s'
                cursor.execute(Select_Query,(Employee_Id,'Rejected'))
                Emp_Rejected_Info=cursor.fetchall()
                print("................upto this...................")
                print("..........",Emp_Rejected_Info)
                if Emp_Rejected_Info:
                   Response_Data={'status':'Success','Emp_Rejected_Info':Emp_Rejected_Info}
                   return jsonify(Response_Data)
                else:
                    Response_Data={'status':'failed','message':'requested_user_id not exist in table..'}
                    return jsonify(Response_Data)
        except Exception as e :
            print("exception occerd in Fetch_Emp_History function and error is:",e)





#..................................................Leave RequestData......................................................
# Returns ALL leave records for an employee: pending (Leave_Request) + history (Leave_history)
@app.route('/get_leaverequest_data', methods=['POST'])
def Fetch_Leave_Request():
    if request.method == 'POST':
        Data = request.get_json()
        print("data is", Data)
        Employee_Id = Data['employee_id']
        try:
            with connection.cursor() as cursor:

                # ── 1. Pending leaves still in Leave_Request ──
                cursor.execute(
                    'SELECT Applied_on, Reason, Start_date, End_date, Request_id, '
                    'Employee_id, Employee_Name, Leave_Type, No_of_Days, Status '
                    'FROM Leave_Request WHERE Employee_id=%s',
                    (Employee_Id,)
                )
                pending_leaves = cursor.fetchall()

                # ── 2. Historical leaves (Accepted/Rejected) from Leave_history ──
                # Note: Leave_history has no Applied_on column — use Start_date as fallback
                cursor.execute(
                    'SELECT Start_date AS Applied_on, Reason, Start_date, End_date, Request_id, '
                    'Employee_id, Employee_Name, Leave_Type, No_of_Days, Status, Approved_By_Whom '
                    'FROM Leave_history WHERE Employee_id=%s',
                    (Employee_Id,)
                )
                history_leaves = cursor.fetchall()

                # ── 3. Combine both — pending first, then history ──
                All_Leaves = list(pending_leaves) + list(history_leaves)

                # ── 4. Convert date objects to strings ──
                for lv in All_Leaves:
                    for field in ('Applied_on', 'Start_date', 'End_date'):
                        if lv.get(field) and hasattr(lv[field], 'strftime'):
                            lv[field] = lv[field].strftime('%Y-%m-%d')

                # Employee count and name list
                cursor.execute('SELECT COUNT(Employee_id) FROM employee_complete_details')
                Employee_Count = cursor.fetchall()
                cursor.execute('SELECT Employee_id, Employee_Name FROM employee_complete_details')
                Emp_Details = cursor.fetchall()

                print(f"Leaves for {Employee_Id}: {len(pending_leaves)} pending, {len(history_leaves)} history")

                Response_Data = {
                    'status': 'Success',
                    'Employee_Leave_request_data': All_Leaves,
                    'Total_employees': Employee_Count,
                    'all_employee_name_id': Emp_Details
                }
                return jsonify(Response_Data)

        except Exception as e:
            print("exception in Fetch_Leave_Request:", e)
            return jsonify({'status': 'failed', 'message': str(e)}), 500





#.................................................LastRecord..............................................................
            
#getting employee_id and sending last record data from leave_request and leave_history
@app.route('/last_record', methods=['POST'])
def Last_Record():
  if request.method == 'POST':
    Data = request.get_json()
    print(Data)       
    Employee_Id=Data['employee_id']
    try:
        with connection.cursor() as cursor: 
         Select_Query='select Start_date,End_date,Applied_on from  Leave_Request  WHERE Employee_id=%s order by applied_on desc limit 1'
         cursor.execute(Select_Query,(Employee_Id))
         Emp_Info=cursor.fetchall()
         print("employee_last_record",Emp_Info)         
         Select_Query='select Status,Start_date,End_date,Approved_By_Whom from Leave_history WHERE Employee_id= %s AND Status="Accepted" order by  End_date desc limit 1 '
         cursor.execute(Select_Query,(Employee_Id))
         Emp_History=cursor.fetchall()
         Select_Query='select Status,Start_date,End_date,Approved_By_Whom from Leave_history WHERE Employee_id= %s AND Status="Rejected" order by  End_date desc limit 1 '
         cursor.execute(Select_Query,(Employee_Id))
         Emp_Leave_Rejected=cursor.fetchall()   

         #sending response(Employee leave_request Information and leave_history information )           
        Response_Data={'status':'Success','Employee_last_record':Emp_Info,'Employee_last_history_details':Emp_History,'Emp_Leave_Rejected':Emp_Leave_Rejected}
        return jsonify(Response_Data) 
    except Exception as e:
        print("error occured in Last_Record")
        return "employee_id not found"
  else:
      print("method not found")
      return "method not found"
 #....................................................Analytics  Dashboard............................................
DB_CONFIG = {
    'host':     '127.0.0.1',       # ← same as your other routes
    'user':     'root',            # ← same as your other routes
    'password': 'shashi14',                # ← same as your other routes
    'database': 'payroll_project',         # ← same as your other routes
    'cursorclass': pymysql.cursors.DictCursor
}

@app.route('/get_analytics_data', methods=['POST'])
def get_analytics_data():
    try:
        data        = request.get_json()
        period_days = int(data.get('period_days', 30))

        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
        today_str   = datetime.now().strftime('%Y-%m-%d')

        db     = pymysql.connect(**DB_CONFIG)
        cursor = db.cursor()

        # ── 1. Total employees ────────────────────────────────
        cursor.execute("SELECT COUNT(Employee_id) AS total FROM Employee_info")
        total_employees = cursor.fetchone()['total']

        # ── 2. All employee names + IDs ───────────────────────
        cursor.execute("SELECT Employee_id, Employee_Name FROM Employee_info")
        all_employees = cursor.fetchall()

        # ── 3. Daily attendance count (last N days) ───────────
        cursor.execute("""
            SELECT DATE(Clock_in_time) AS date, COUNT(DISTINCT Employee_id) AS count
            FROM Attendance_info
            WHERE DATE(Clock_in_time) >= %s
            GROUP BY DATE(Clock_in_time)
            ORDER BY date ASC
        """, (cutoff_date,))
        daily_attendance = cursor.fetchall()
        for row in daily_attendance:
            if hasattr(row['date'], 'strftime'):
                row['date'] = row['date'].strftime('%Y-%m-%d')

        # ── 4. Per-employee attendance summary ────────────────
        cursor.execute("""
            SELECT
                e.Employee_id   AS employee_id,
                e.Employee_Name AS employee_name,
                COUNT(DISTINCT DATE(a.Clock_in_time)) AS present_days,
                0 AS absent_days
            FROM Employee_info e
            LEFT JOIN Attendance_info a
                ON e.Employee_id = a.Employee_id
                AND DATE(a.Clock_in_time) >= %s
            GROUP BY e.Employee_id, e.Employee_Name
            ORDER BY present_days DESC
        """, (cutoff_date,))
        attendance_summary = cursor.fetchall()

        # ── 5. Leave requests ─────────────────────────────────
        cursor.execute("""
            SELECT
                Employee_Name, Employee_id,
                Leave_type, Start_date, End_date,
                No_of_days, Status, Applied_on
            FROM Leave_Request
            WHERE Applied_on >= %s
            ORDER BY Applied_on DESC
        """, (cutoff_date,))
        leave_requests = cursor.fetchall()
        for row in leave_requests:
            for field in ('Start_date', 'End_date', 'Applied_on'):
                if row.get(field) and hasattr(row[field], 'strftime'):
                    row[field] = row[field].strftime('%Y-%m-%d')

        # ── 6. WFH summary per employee ───────────────────────
        cursor.execute("""
            SELECT
                Employee_Name,
                Employee_id,
                COUNT(*) AS wfh_days,
                0        AS office_days
            FROM WFH_Info
            WHERE From_date >= %s AND Status = 'Approved'
            GROUP BY Employee_id, Employee_Name
            ORDER BY wfh_days DESC
        """, (cutoff_date,))
        wfh_summary = cursor.fetchall()

        # ── 7. WFH active today ───────────────────────────────
        cursor.execute("""
            SELECT COUNT(*) AS count FROM WFH_Info
            WHERE From_date <= %s AND To_date >= %s AND Status = 'Approved'
        """, (today_str, today_str))
        wfh_today = cursor.fetchone()['count']

        # ── 8. Leave status counts ────────────────────────────
        cursor.execute("""
            SELECT Status, COUNT(*) AS count
            FROM Leave_Request
            WHERE Applied_on >= %s
            GROUP BY Status
        """, (cutoff_date,))
        leave_status = {row['Status']: row['count'] for row in cursor.fetchall()}

        cursor.close()
        db.close()

        return jsonify({
            'status':            'success',
            'total_employees':   total_employees,
            'all_employees':     all_employees,
            'daily_attendance':  daily_attendance,
            'attendance_summary': attendance_summary,
            'leave_requests':    leave_requests,
            'wfh_summary':       wfh_summary,
            'wfh_today':         wfh_today,
            'leave_status':      leave_status,
        })

    except Exception as e:
        print("Analytics error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500




#....................................................Attendance Data............................................................
#getting id and sending employee_attendance_info based on id and date.......
@app.route('/get_clock_in', methods=['POST'])
def specific_attendance_details():
    Data = request.get_json()
    Employee_Id = Data['employee_id']

    today = datetime.now().date()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT clock_in_time FROM Employee_Attendance_Data WHERE Employee_id=%s AND Date=%s",
            (Employee_Id, today)
        )
        Emp_Info = cursor.fetchone()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM employee_complete_details WHERE Employee_id=%s",
            (Employee_Id,)
        )
        Profile_Info = cursor.fetchone()

    # ✅ FORMAT DATE FIELDS MANUALLY
    if Profile_Info and Profile_Info.get('Date'):
        Profile_Info['Date'] = Profile_Info['Date'].strftime('%Y-%m-%d')

    if Profile_Info and Profile_Info.get('Date_of_birth'):
        Profile_Info['Date_of_birth'] = Profile_Info['Date_of_birth']

    if Emp_Info:
        Clock_In_Time = str(Emp_Info['clock_in_time'])
        return jsonify({
            'status': 'Success',
            'current_time': Clock_In_Time,
            'current_date': today.strftime('%b %d, %Y'),
            'Profile_Info': Profile_Info
        })

    return jsonify({
        'status': 'failed',
        'current_date': today.strftime('%b %d, %Y'),
        'Profile_Info': Profile_Info
    })
#....................................................Emp CountIdsNames................................................       
#sending employee count ,employee id and names......
@app.route('/get_employees_count_admin',methods=['POST'])
def Fetch_Emp_Count_Info():
    if request.method=='POST':
        Data = request.get_json()
        print("this is data from get_employees_count",Data)

        try:
          if Data: 
            Date = datetime.now().date()
            print("this is date",Date)
            Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
            No_Of_Days=1
            Last_Day_Date = Date - timedelta(days=No_Of_Days)
            Last_Day_Date_Formatted = Last_Day_Date.strftime('%Y-%m-%d')
            # Date=Date-no_of_days
            print("last day is:",Last_Day_Date_Formatted)      
            with connection.cursor() as cursor:
        #fetching employee_count......... 
             Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
             cursor.execute(Count_Query)
             Employee_Count=cursor.fetchall()
        #selecting all employee_ids and names
            with connection.cursor() as cursor:
             Select_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
             cursor.execute(Select_Query)  
             Emp_Info = cursor.fetchall()
             print("EMP_INFO FROM employee_complete_details:", Emp_Info)
            with connection.cursor() as cursor:
             Select_Query='SELECT Employee_id,employee_name,clock_in_time,clock_out_time,clock_in_location,Avg_working_hrs FROM Employee_Attendance_Data WHERE Date=%s'
             cursor.execute(Select_Query,(Present_Formatted_Date))
             Clock_Info=cursor.fetchall()
             print("clock information",Clock_Info)
            for i in range(len(Clock_Info)):
              clock_in_time=str(Clock_Info[i]['clock_in_time'])
              clock_out_time=str(Clock_Info[0]['clock_out_time'])
              Avg_working_hrs=str(Clock_Info[0]['Avg_working_hrs'])
              Clock_Info[i]['clock_in_time']=clock_in_time
              Clock_Info[i]['clock_out_time']=clock_out_time
              Clock_Info[i]['Avg_working_hrs']=Avg_working_hrs 
            with connection.cursor() as cursor:
              # Pending leaves (Waiting)
              cursor.execute(
                  'SELECT Employee_id,Employee_Name,Applied_on,Start_date,End_date,'
                  'No_of_Days,Leave_Type,Reason,Request_id,Status '
                  'FROM Leave_Request WHERE Status=%s',
                  ('Waiting',)
              )
              pending_info = cursor.fetchall()
              # Convert date objects to strings for JSON
              for lv in pending_info:
                  for f in ('Applied_on','Start_date','End_date'):
                      if lv.get(f) and hasattr(lv[f],'strftime'):
                          lv[f] = lv[f].strftime('%Y-%m-%d')
              Leave_Request_Info = pending_info
            with connection.cursor() as cursor:
              Select_Query='SELECT Request_id,Employee_id,Employee_Name,Applied_on,Start_Date,End_Date,No_of_Days,Reason,Status FROM Work_From_Home WHERE Status=%s'
              cursor.execute(Select_Query,('Waiting',))
              Work_From_Home_Info=cursor.fetchall()
              print("work_from_home_info", Work_From_Home_Info)
            with connection.cursor() as cursor:
              Select_Query='SELECT Employee_id,Employee_Name, Status_Update,Issues,Completed_Task,Feature_Targets FROM Daily_Status_Update Where Date=%s'
              cursor.execute(Select_Query,Present_Formatted_Date)
              Daily_Status_Info=cursor.fetchall()
              print("Daily_Status_Info", Daily_Status_Info)
            #sending response (employee count and their ids and names.........)
              Response_Data={'status':'Success','Total_employees':Employee_Count,'all_employee_name_id':Emp_Info,'Clock_Info':Clock_Info,'Leave_Request_Info':Leave_Request_Info,'Work_From_Home_Info':Work_From_Home_Info,'Daily_Status_Info':Daily_Status_Info}
              return jsonify(Response_Data)
          else:
            Response_Data={'status':'failed'}
            return jsonify(Response_Data)
        except Exception as e:
            print("exception is",e)
            Response_Data={'status':'failed'}
            return jsonify(Response_Data)
#....................................................Attendance Data.....................................................................
#sending employee_attendance info based on id along with employee count& their id_names......
@app.route('/get_employee_attendance',methods=['POST'])
def employee_attendance_data():
    if request.method=='POST':
        Data = request.get_json()
        Employee_Id=Data['employee_id']
        print(Data)
        try:
             if Data:       
               with connection.cursor() as cursor: 
                #selecting clock info from attendance table..
                Select_Query='SELECT Date,clock_in_time,clock_out_time,clock_in_location,Avg_working_hrs,employee_name,Employee_id FROM Employee_Attendance_Data WHERE Employee_id=%s'
                cursor.execute(Select_Query,(Employee_Id))
                Clock_Info=cursor.fetchall()
                #fetching employee count......
                Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                cursor.execute(Count_Query)
                Employee_Count=cursor.fetchall()
                 #selecting all employee_ids and names
                Select_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                cursor.execute(Select_Query)  
                Emp_Info = cursor.fetchall()
                print(Clock_Info)
                print(Employee_Count)
                print(Emp_Info)
                for i in range(len(Clock_Info)):
                    Date=str(Clock_Info[i]['Date'])
                    clock_in_time=str(Clock_Info[i]['clock_in_time'])
                    clock_out_time=str(Clock_Info[0]['clock_out_time'])
                    Avg_working_hrs=str(Clock_Info[0]['Avg_working_hrs'])
                    Clock_Info[i]['Date']=Date
                    Clock_Info[i]['clock_in_time']=clock_in_time
                    Clock_Info[i]['clock_out_time']=clock_out_time
                    Clock_Info[i]['Avg_working_hrs']=Avg_working_hrs 
                    #sending response(employee count employee_clock info and all employee_ids and names)          
                Response_Data={'status':'Success','employee_clock_info':Clock_Info,'Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
                return jsonify(Response_Data)
             else:
                  Response_Data={'status':'failed','message':'requested_employee not there in records...','Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
                  return jsonify(Response_Data)
        except Exception as e:
            print("exception is",e)
            Response_Data={'status':'failed','message':'exception occured..'}
            return jsonify(Response_Data)





#.....................................................Last MonthWeekDay......................................................
#sending employe daily status data based on request type(last month,last week or last day)
@app.route('/admin_get_status',methods=['POST'])
def Fetch_Fest_Info():
    if request.method == 'POST':
        Data = request.get_json()
        Request_Type=Data['Request_Type']
        Employee_Id=Data['Emp_id']
        print(Data)
        try:
          if Request_Type=='Last_Month':
           try:
             with connection.cursor() as cursor:   
              Date = datetime.now().date()
              Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
              No_Of_Days=30
              Last_Month_Date = Date - timedelta(days=No_Of_Days)
              Last_Month_Date_Formatted = Last_Month_Date.strftime('%Y-%m-%d')
            # Date=Date-no_of_days
              print("last month date is:",Last_Month_Date_Formatted)
            #selecting specific info based on present and before one month dates....                 
              Select_Query="SELECT Date,Employee_id,Employee_Name,Status_Update,Issues,Completed_Task,Feature_Targets FROM Daily_Status_Update WHERE Date BETWEEN %s AND %s AND Employee_id=%s"
              cursor.execute(Select_Query,(Last_Month_Date_Formatted,Present_Formatted_Date,Employee_Id))  
              Status_Info = cursor.fetchall()
              print("data is:",Status_Info) 
              Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
              cursor.execute(Count_Query)
              Employee_Count=cursor.fetchall()
              Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
              cursor.execute(Employee_Id_Name_Query)  
              Employee_Id_Names = cursor.fetchall()
            #sending response (Attendance information.........)
              Response_Data={'status':'Success','Status_Info':Status_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
              return jsonify(Response_Data)
           except Exception as e:
            print("exception occerd in  and error is",e)
            Response_Data={'status':'failed','Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
            return jsonify(Response_Data)
                 
          elif Request_Type=='Last_week':
           try:
              with connection.cursor() as cursor:   
                Date = datetime.now().date()
                Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
                No_Of_Days=7
                Last_Week_Date = Date - timedelta(days=No_Of_Days)
                Last_Week_Date_Formatted = Last_Week_Date.strftime('%Y-%m-%d')
               # Date=Date+no_of_days
                print("last weekdate is:",Last_Week_Date_Formatted)
               #selecting specific info based on present and before one week dates....                 
                Select_Query="SELECT Date,Employee_id,Employee_Name,Status_Update,Issues,Completed_Task,Feature_Targets FROM Daily_Status_Update WHERE Date BETWEEN %s AND %s AND Employee_id=%s"
                cursor.execute(Select_Query,(Last_Week_Date_Formatted,Present_Formatted_Date,Employee_Id))  
                Status_Info = cursor.fetchall()
                print("data is:",Status_Info) 
                Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                cursor.execute(Count_Query)
                Employee_Count=cursor.fetchall()
                Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                cursor.execute(Employee_Id_Name_Query)  
                Employee_Id_Names = cursor.fetchall()
            #sending response (Attendance information.........)
              Response_Data={'status':'Success','Status_Info':Status_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
              return jsonify(Response_Data)
           except Exception as e:
            print("exception occerd in  and error is",e)
            Response_Data={'status':'failed','Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
            return jsonify(Response_Data)
          
          elif Request_Type=='Last_day':
              with connection.cursor() as cursor:   
                Date = datetime.now().date()
                Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
                No_Of_Days=1
                Last_Day_Date = Date - timedelta(days=No_Of_Days)
                Last_Day_Date_Formatted = Last_Day_Date.strftime('%Y-%m-%d')
               # Date=Date-no_of_days
                print("last day is:",Last_Day_Date_Formatted)
               #selecting specific info based on present and before one day dates....                 
                Select_Query="SELECT Date,Employee_id,Employee_Name,Status_Update,Issues,Completed_Task,Feature_Targets FROM Daily_Status_Update WHERE Date= %s AND Employee_id=%s"
                cursor.execute(Select_Query,(Last_Day_Date_Formatted,Employee_Id))  
                Status_Info = cursor.fetchall()
                print("data is:",Status_Info) 
              #sending response (festival information.........)
                Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                cursor.execute(Count_Query)
                Employee_Count=cursor.fetchall()
                Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                cursor.execute(Employee_Id_Name_Query)  
                Employee_Id_Names = cursor.fetchall()
            #sending response (Attendance information.........)
                Response_Data={'status':'Success','Status_Info':Status_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
              return jsonify(Response_Data)
          else:
            Response_Data={'status':'failed','message':'invalid request_type'}
            return jsonify(Response_Data)
        except Exception as e:
            print("exception occerd in  and error is",e)
            Response_Data={'status':'failed','Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
            return jsonify(Response_Data)





#.....................................................Last MonthWeekDay......................................................
#sending employe Attendance  data based on request type(last month,last week or last day)
@app.route('/admin_get_attendance',methods=['POST'])
def Fetch_Attendance_Info():
  if request.method == 'POST':
    Data = request.get_json()
    Request_Type=Data['Request_Type']
    Employee_Id=Data['Emp_id']
    print(Data)
    with connection.cursor() as cursor:
      Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
      cursor.execute(Count_Query)
      Emp_Count=cursor.fetchall()
      print("employee count",Emp_Count)
      Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
      cursor.execute(Employee_Id_Name_Query)  
      Employee_Id_Name = cursor.fetchall()
      print("employee id names..",Employee_Id_Name)
      try:
        if Request_Type=='Last_Month':   
          Date = datetime.now().date()
          Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
          print("present date is",Present_Formatted_Date)
          No_Of_Days=30
          Last_Month_Date = Date - timedelta(days=No_Of_Days)
          Last_Month_Date_Formatted = Last_Month_Date.strftime('%Y-%m-%d')
        # Date=Date-no_of_days
          print("last month date is:",Last_Month_Date_Formatted)
            #selecting specific info based on present and before one month dates....                
                #selecting clock info from attendance table..
          with connection.cursor() as cursor:
              Select_Query='SELECT Date,employee_name,clock_in_time,clock_out_time,clock_in_location,Avg_working_hrs FROM Employee_Attendance_Data WHERE Date BETWEEN %s AND %s AND Employee_id=%s'
              cursor.execute(Select_Query,(Last_Month_Date_Formatted,Present_Formatted_Date,Employee_Id))
              Clock_Info=cursor.fetchall()
              print("data is:",Clock_Info)
              try: 
              #converting clocks into required time formates...
                  for i in range(len(Clock_Info)):
                      Date=str(Clock_Info[i]['Date'])
                      Clock_In_Time=str(Clock_Info[i]['clock_in_time'])
                      Clock_Out_Time=str(Clock_Info[0]['clock_out_time'])
                      Avg_Working_Hrs=str(Clock_Info[0]['Avg_working_hrs'])
                      Clock_Info[i]['Date']=Date
                      Clock_Info[i]['clock_in_time']=Clock_In_Time
                      Clock_Info[i]['clock_out_time']=Clock_Out_Time
                      Clock_Info[i]['Avg_working_hrs']=Avg_Working_Hrs
                      Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                      cursor.execute(Count_Query)
                      Employee_Count=cursor.fetchall()
                      Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                      cursor.execute(Employee_Id_Name_Query)  
                      Employee_Id_Names = cursor.fetchall()
            #sending response (Attendance information.........)
                  Response_Data={'status':'Success','Clock_Info':Clock_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
                  return jsonify(Response_Data)
              except Exception as e:
                    print("exception occured in Last_Month n error is ",e)
                    Response_Data={'status':'failed','Employee_Count':Emp_Count,'All_Names_Ids':Employee_Id_Name}
              return jsonify(Response_Data)
        elif Request_Type=='Last_week':
            with connection.cursor() as cursor:   
                Date = datetime.now().date()
                Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
                No_Of_Days=7
                Last_Week_Date = Date - timedelta(days=No_Of_Days)
                Last_Week_Date_Formatted = Last_Week_Date.strftime('%Y-%m-%d')
               # Date=Date+no_of_days
                print("last weekdate is:",Last_Week_Date_Formatted)
               #selecting specific info based on present and before one week dates....                 
                Select_Query='SELECT Date,employee_name,clock_in_time,clock_out_time,clock_in_location,Avg_working_hrs FROM Employee_Attendance_Data WHERE Date BETWEEN %s AND %s AND Employee_id=%s'
                cursor.execute(Select_Query,(Last_Week_Date_Formatted,Present_Formatted_Date,Employee_Id))  
                Clock_Info = cursor.fetchall()
                print("data is:",Clock_Info) 
                try:
                    for i in range(len(Clock_Info)):
                      Date=str(Clock_Info[i]['Date'])
                      Clock_In_Time=str(Clock_Info[i]['clock_in_time'])
                      Clock_Out_Time=str(Clock_Info[0]['clock_out_time'])
                      Avg_Working_Hrs=str(Clock_Info[0]['Avg_working_hrs'])
                      Clock_Info[i]['Date']=Date
                      Clock_Info[i]['clock_in_time']=Clock_In_Time
                      Clock_Info[i]['clock_out_time']=Clock_Out_Time
                      Clock_Info[i]['Avg_working_hrs']=Avg_Working_Hrs
                  #sending response (festival information.........)
                      with connection.cursor() as cursor:
                        Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                        cursor.execute(Count_Query)
                        Employee_Count=cursor.fetchall()
                        Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                        cursor.execute(Employee_Id_Name_Query)  
                        Employee_Id_Names = cursor.fetchall()
              #sending response (festival information.........)
                        Response_Data={'status':'Success','Clock_Info':Clock_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
                        return jsonify(Response_Data)
                except Exception as e:
                    print("exception occured in Last_week n error is ",e)
                    Response_Data={'status':'failed','Employee_Count':Emp_Count,'All_Names_Ids':Employee_Id_Name}
                return jsonify(Response_Data)
                
        elif Request_Type=='Last_day':
              with connection.cursor() as cursor:   
                Date = datetime.now().date()
                Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
                No_Of_Days=1
                Last_Day_Date = Date - timedelta(days=No_Of_Days)
                Last_Day_Date_Formatted = Last_Day_Date.strftime('%Y-%m-%d')
               # Date=Date-no_of_days
                print("last day is:",Last_Day_Date_Formatted)
               #selecting specific info based on present and before one day dates....                 
                Select_Query='SELECT employee_name,clock_in_time,clock_out_time,clock_in_location,Avg_working_hrs FROM Employee_Attendance_Data WHERE Date=%s AND Employee_id=%s'
                cursor.execute(Select_Query,(Last_Day_Date_Formatted,Employee_Id))  
                Clock_Info = cursor.fetchall()
                print("data is:",Clock_Info) 
                try:
                    for i in range(len(Clock_Info)):
                      Date=str(Clock_Info[i]['Date'])
                      Clock_In_Time=str(Clock_Info[i]['clock_in_time'])
                      Clock_Out_Time=str(Clock_Info[0]['clock_out_time'])
                      Avg_Working_Hrs=str(Clock_Info[0]['Avg_working_hrs'])
                      Clock_Info[i]['Date']=Date
                      Clock_Info[i]['clock_in_time']=Clock_In_Time
                      Clock_Info[i]['clock_out_time']=Clock_Out_Time
                      Clock_Info[i]['Avg_working_hrs']=Avg_Working_Hrs
              #sending response (festival information.........)
                      with connection.cursor() as cursor:
                        Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                        cursor.execute(Count_Query)
                        Employee_Count=cursor.fetchall()
                        Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                        cursor.execute(Employee_Id_Name_Query)  
                        Employee_Id_Names = cursor.fetchall()
              #sending response (festival information.........)
                        Response_Data={'status':'Success','Clock_Info':Clock_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
                        return jsonify(Response_Data)
                except Exception as e:
                    print("exception occured in Last_Month n error is ",e)
                    Response_Data={'status':'failed','Employee_Count':Emp_Count,'All_Names_Ids':Employee_Id_Name}
                return jsonify(Response_Data)  
      except Exception as e:
            print("exception occerd in Fetch_Attendance_Info function and error is",e,)
            Response_Data={'status':'failed','Employee_Count':Emp_Count,'All_Names_Ids':Employee_Id_Name}
            return jsonify(Response_Data)  
  else:
      print("invalid request type..")
      
     




#.....................................................Last MonthWeekDay......................................................
#sending employe leave_status data based on request type(last month,last week or last day)
@app.route('/admin_get_Leave_status',methods=['POST'])
def Fetch_LeaveStatus_Info():
    if request.method == 'POST':
        Data = request.get_json()
        Request_Type=Data['Request_Type']
        Employee_Id=Data['Emp_id']
        print(Data)
        try:
          if Request_Type=='Last_Month':
           try:
             with connection.cursor() as cursor:   
              Date1 = datetime.now().date()
              Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
              No_Of_Days=30
              Last_Month_Date = Date1 - timedelta(days=No_Of_Days)
              Last_Month_Date_Formatted = Last_Month_Date.strftime('%Y-%m-%d')
            # Date=Date-no_of_days
              print("last month date is:",Last_Month_Date_Formatted)
            #selecting specific info based on present and before one month dates....                 
              Select_Query="SELECT Employee_id,Employee_Name,Applied_on,Start_date,End_date,Reason FROM Leave_Request WHERE Date BETWEEN %s AND %s AND Employee_id=%s"
              cursor.execute(Select_Query,(Last_Month_Date_Formatted,Present_Formatted_Date,Employee_Id))  
              Leave_Status_Info = cursor.fetchall()
              print("data is:",Leave_Status_Info) 
              Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
              cursor.execute(Count_Query)
              Employee_Count=cursor.fetchall()
              Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
              cursor.execute(Employee_Id_Name_Query)  
              Employee_Id_Names = cursor.fetchall()
            #sending response (Attendance information.........)
              Response_Data={'status':'Success','Leave_Status_Info':Leave_Status_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
              return jsonify(Response_Data)
           except Exception as e:
            print("exception occerd in  and error is",e)
            Response_Data={'status':'failed','Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
            return jsonify(Response_Data)
                  
          elif Request_Type=='Last_week':
           try:
              with connection.cursor() as cursor:   
                Date = datetime.now().date()
                Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
                No_Of_Days=7
                Last_Week_Date = Date - timedelta(days=No_Of_Days)
                Last_Week_Date_Formatted = Last_Week_Date.strftime('%Y-%m-%d')
               # Date=Date+no_of_days
                print("last weekdate is:",Last_Week_Date_Formatted)
               #selecting specific info based on present and before one week dates....                 
                Select_Query="SELECT Employee_id,Employee_Name,Applied_on,Start_date,End_date,Reason FROM Leave_Request WHERE Date BETWEEN %s AND %s AND Employee_id=%s"
                cursor.execute(Select_Query,(Last_Week_Date_Formatted,Present_Formatted_Date,Employee_Id))  
                Leave_Status_Info = cursor.fetchall()
                print("data is:",Leave_Status_Info) 
                Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                cursor.execute(Count_Query)
                Employee_Count=cursor.fetchall()
                Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                cursor.execute(Employee_Id_Name_Query)  
                Employee_Id_Names = cursor.fetchall()
            #sending response (Attendance information.........)
              Response_Data={'status':'Success','Leave_Status_Info':Leave_Status_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
              return jsonify(Response_Data)
           except Exception as e:
            print("exception occured: ",e)
            Response_Data={'status':'failed','Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
            return jsonify(Response_Data)
          
          elif Request_Type=='Last_day':
              with connection.cursor() as cursor:   
                Date = datetime.now().date()
                Present_Formatted_Date= datetime.now().strftime('%Y-%m-%d')
                No_Of_Days=1
                Last_Day_Date = Date - timedelta(days=No_Of_Days)
                Last_Day_Date_Formatted = Last_Day_Date.strftime('%Y-%m-%d')
               # Date=Date-no_of_days
                print("last day is:",Last_Day_Date_Formatted)
               #selecting specific info based on present and before one day dates....                 
                Select_Query="SELECT Employee_id,Employee_Name,Status_Update,Issues,Completed_Task,Feature_Targets FROM Daily_Status_Update WHERE Date= %s AND Employee_id=%s"
                cursor.execute(Select_Query,(Last_Day_Date_Formatted,Employee_Id))  
                Leave_Status_Info = cursor.fetchall()
                print("data is:",Leave_Status_Info) 
              #sending response (festival information.........)
                Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                cursor.execute(Count_Query)
                Employee_Count=cursor.fetchall()
                Employee_Id_Name_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                cursor.execute(Employee_Id_Name_Query)  
                Employee_Id_Names = cursor.fetchall()
            #sending response (Attendance information.........)
                Response_Data={'status':'Success','Leave_Status_Info':Leave_Status_Info,'Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
              return jsonify(Response_Data)
          else:
            Response_Data={'status':'failed','message':'invalid request_type'}
            return jsonify(Response_Data)
        except Exception as e:
            print("exception occerd in  and error is",e)
            Response_Data={'status':'failed','Employee_Count':Employee_Count,'All_Names_Ids':Employee_Id_Names}
            return jsonify(Response_Data)


#...........................................................FestInfo..............................................................
#getting id and sending employee_leave balance info based on id .......
@app.route('/fest_info',methods=['POST'])
def Fetch_Status_Fest_Info():
    print("hi mamatha how are you")
    if request.method=='POST':
        Data = request.get_json()
        print(Data)       
        Employee_Id=Data['employee_id']
        #selecting leaves from leave balance based on the employee_id.........
        with connection.cursor() as cursor: 
         try:
           Select_Query='select Employee_Name,Sick_Leave,Wedding_Leave,Maternity_Leave,Paternity_Leave,No_of_leaves,Taken_leaves,Pending_leaves FROM  Leave_balance WHERE Employee_id=%s'
           cursor.execute(Select_Query,(Employee_Id))
           Leave_Balance_Info=cursor.fetchall() 
           #selecting fwestival info from holiday table.... 
           Select_Query='SELECT * FROM Holiday'
           cursor.execute(Select_Query)
           Fest_Info=cursor.fetchall()
           print("Leave_Balance_Info",Leave_Balance_Info)
           print("Fest_Info",Fest_Info)

          #  Select_Query='SELECT Date_of_Birth FROM employee_complete_details WHERE MONTH(Date_of_Birth) >= MONTH(CURDATE())  AND DAYOFMONTH(Date_of_Birth) >= DAYOFMONTH(CURDATE())';

          #  cursor.execute(Select_Query)
          #  Birth_Info=cursor.fetchall()
          #  print("Birthday222", Birth_Info)
           #sending fest and balance info..........  


           Info_From_Specific=Specific_Info()
        
           Employee_Names_Dob=Info_From_Specific[0]
           History_Info=Info_From_Specific[1]
           Holiday_info=Info_From_Specific[2]
           Announcement_Info=Info_From_Specific[3]
           print("complete_information",Info_From_Specific[0]) 
           Response_Data = {'status':'Success','Leave_Balance_Info':Leave_Balance_Info,'Fest_Info':Fest_Info,
                                    "date_of_births":Employee_Names_Dob,"leaves_info":History_Info,"holiday_info":Holiday_info,
                                    "announcement_info":Announcement_Info} 

          #  Response_Data={'status':'Success','Leave_Balance_Info':Leave_Balance_Info,'Fest_Info':Fest_Info}
           return jsonify(Response_Data) 
         except Exception as e:
            print("exception is",e)
            Response_Data={'status':'failed','message':'id not found'}
            return jsonify(Response_Data)
    else:
        print("method not found")
        return "method not found"
             

#...........................................................FestInfo..............................................................
#getting id and sending employee_leave balance info based on id .......
@app.route('/Admin_fest_info',methods=['POST'])
def Fetch_holiday_Info():
    if request.method=='POST':
        Data = request.get_json()
        print(Data)       
        Employee_Id=Data['employee_id']
        #selecting leaves from leave balance based on the employee_id.........
        with connection.cursor() as cursor: 
         try:
           #selecting fwestival info from holiday table.... 
           Select_Query='SELECT * FROM Holiday'
           cursor.execute(Select_Query)
           Fest_Info=cursor.fetchall()
           print("Fest_Info",Fest_Info)
           #sending fest and balance info..........  
           Info_From_Specific=Specific_Info()
           Employee_Names_Dob=Info_From_Specific[0]
           History_Info=Info_From_Specific[1]
           Holiday_info=Info_From_Specific[2]
           Announcement_Info=Info_From_Specific[3]
           print("complete_information",Info_From_Specific) 
           Response_Data = {'status':'Success','Fest_Info':Fest_Info,
                                    "date_of_births":Employee_Names_Dob,"leaves_info":History_Info,"holiday_info":Holiday_info,
                                    "announcement_info":Announcement_Info} 

          #  Response_Data={'status':'Success','Leave_Balance_Info':Leave_Balance_Info,'Fest_Info':Fest_Info}
           return jsonify(Response_Data) 
         except Exception as e:
            print("exception is",e)
            Response_Data={'status':'failed','message':'id not found'}
            return jsonify(Response_Data)
    else:
        print("method not found")
        return "method not found"






#...................................................LeaveRequest for WorkFromHome ...........................................................
#getting leave request data..........   
def Generate_Req_Id():
    return ''.join([str(random.randint(0, 9)) for _ in range(3)])     
    
@app.route('/work_from_home', methods=['POST'])
def Work_From_Home():
        if request.method == 'POST':
          data = request.get_json()
          print(data)
          employee_id=data['id']
          employee_name=data['employee_name']
          Start_date=data['from_date']
          End_date=data['to_date']
          Reason=data['reason']
          Req_Id=Generate_Req_Id()
          Req_Id=str(Req_Id)
          print(data)
          request_type=data['request_type']
          with connection.cursor() as cursor: 
            current_date= datetime.now().strftime('%Y-%m-%d')
      # Current_Date=str(datetime.now().strftime('%Y-%m-%d'))
            Select_Query='select * FROM Employee_Attendance_Data WHERE Employee_id=%s AND Date=%s'
            cursor.execute(Select_Query,( employee_id,current_date))
            Exist_Data=cursor.fetchone()
            clock_in_time_str=""
            print("upto this1")
            try:
              clock_in_time_str=str(Exist_Data['clock_in_time'])
      #   clock_in_time_str = datetime.strptime(Exist_Data['clock_in_time'], "%H:%M:%S")
              print("upto this2")
            except:
              clock_in_time_str="" 
          with connection.cursor() as cursor:                       
            select_employe = "SELECT Team_lead_email,Manager_email,Team_lead ,Manager_name FROM  employee_complete_details  WHERE Employee_id = %s "
            cursor.execute(select_employe , (employee_id,))  
            employe_row = cursor.fetchone()
            print("employee data",employe_row)
            Team_lead_email=employe_row['Team_lead_email']
            Manager_email=employe_row['Manager_email']
            Team_lead=employe_row['Team_lead']
            Manager_name=employe_row['Manager_name']
            print("team lead emails",Team_lead_email,Manager_email) 
            End_date = datetime.strptime(End_date, '%Y-%m-%d')
            Start_date = datetime.strptime(Start_date, '%Y-%m-%d')
            No_of_Days=(End_date - Start_date).days
            Applied_On=datetime.now().strftime('%Y-%m-%d')
            if request_type=="insert":
                  print("this is insert function",Start_date,End_date)
                  print("applied_on...",Applied_On)
                  with connection.cursor() as cursor:
                    print("up to this1")
                    insert_into_leave_request= "INSERT INTO Work_From_Home (Request_id,Employee_id,Employee_Name,Start_Date,End_Date,No_of_Days,Reason,Status,Team_lead,Manager_name,Team_lead_email,Manager_email,Applied_on) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(insert_into_leave_request, (Req_Id,employee_id,employee_name,Start_date,End_date,No_of_Days,Reason,"Waiting",Team_lead,Manager_name,Team_lead_email,Manager_email,Applied_On))
                    print("up to this2")

                    connection.commit()
                    print("upto this 3")       
                    # response={'status':"success",'message':"leave_request data inserted successfully..."}
                    # return jsonify(response)
                    html = render_template_string(
                                                  """
                                                    <p>Dear {{person_name}},

                                                    <p>Subject: Request for Work From Home</p>
                                                    <p>I trust this message finds you well. I am writing to respectfully request the opportunity to work from home for the following dates:</p>
                                                    <p>Start Date: <strong>{{ Start_date }}</strong></p>
                                                    <p>End Date: <strong>{{ End_date }}</strong></p>
                                                    <p>Total Number of Days: <strong>{{ No_of_Days }}</strong></p>
                                                    <p>Reason for Work From Home: <strong>{{ Reason }}</strong></p>

                                                    <p>Given the nature of my role and current circumstances, I am confident that working from home will not only allow me to maintain the same level of productivity but also offer a conducive environment to focus on key tasks.</p>

                                                   <p> I assure you of my commitment to meet all deadlines and remain accessible during standard working hours for any necessary discussions or updates.</p>

                                                    <p>Should you require any additional information or have specific guidelines for remote work, I am more than willing to accommodate and provide the necessary support to facilitate this request.</p>

                                                   <p><strong> Thank you for considering my proposal. Your understanding and support are deeply appreciated.</strong></p>

                                                    <p>Warm regards,</p>
                                                   <p> {{employee_name}}</p>

                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name, _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(Req_Id),
                                                 person_name=Team_lead,
                                                 Start_date=Start_date,
                                                 End_date=End_date,
                                                 Reason=Reason,
                                                 No_of_Days=No_of_Days,
                                                 employee_name=employee_name,
                                                 )
                    msg_team_lead = Message(
                                    'Leave Request',
                    sender='enerziff@gmail.com',
                    recipients=[Team_lead_email]
                    )
                    msg_team_lead.body = "You have got a leave request for Work From Home from " + employee_name + "  Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                    msg_team_lead.html = html
                    try:
                        mail.send(msg_team_lead)
                        print("mail sent to team_lead")
                    except Exception as e:
                        print("WFH team lead email error (non-fatal):", e)

                    # Send email to manager
                    html = render_template_string(
                                                  """
                                                  <p>Dear {{person_name}},

                                                    <p>Subject: Request for Work From Home</p>
                                                    <p>I trust this message finds you well. I am writing to respectfully request the opportunity to work from home for the following dates:</p>
                                                    <p>Start Date: <strong>{{ Start_date }}</strong></p>
                                                    <p>End Date: <strong>{{ End_date }}</strong></p>
                                                    <p>Total Number of Days: <strong>{{ No_of_Days }}</strong></p>
                                                    <p>Reason for Work From Home: <strong>{{ Reason }}</strong></p>

                                                    <p>Given the nature of my role and current circumstances, I am confident that working from home will not only allow me to maintain the same level of productivity but also offer a conducive environment to focus on key tasks.</p>

                                                   <p> I assure you of my commitment to meet all deadlines and remain accessible during standard working hours for any necessary discussions or updates.</p>

                                                    <p>Should you require any additional information or have specific guidelines for remote work, I am more than willing to accommodate and provide the necessary support to facilitate this request.</p>

                                                   <p><strong> Thank you for considering my proposal. Your understanding and support are deeply appreciated.</strong></p>

                                                    <p>Warm regards,</p>
                                                   <p>{{employee_name}}</p>
                                                   <p>

                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(Req_Id),
                                                 person_name=Manager_name,
                                                 Start_date=Start_date,
                                                 End_date=End_date,
                                                 Reason=Reason,
                                                 No_of_Days=No_of_Days,
                                                 employee_name=employee_name,   
                                                 )
                    msg_manager = Message(
                    'Leave Request',
                    sender='enerziff@gmail.com',
                    recipients=[Manager_email]
                    )
                    msg_manager.body = "You have got a leave request for Work From Home from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                    msg_manager.html = html
                    try:
                        mail.send(msg_manager)
                        print("mail sent to manager")
                    except Exception as e:
                        print("WFH manager email error (non-fatal):", e)
                    current_date= datetime.now().strftime('%Y-%m-%d')
                  response={'status':"success",'From_date':Start_date,'To_date':End_date,'Applied_on':current_date,'clock_in_time':clock_in_time_str,}
                  return jsonify(response)


            elif request_type == "update":
                        print("this is update function", Start_date, End_date)
                        with connection.cursor() as cursor:
                          sql='SELECT Request_id FROM Leave_Request WHERE Employee_id=%s'
                          cursor.execute(sql,(employee_id))
                          query=cursor.fetchone()
                          request_id=query['Request_id']
                          update_sql = "UPDATE Work_From_Home SET Start_Date=%s, End_Date=%s, No_of_Days=%s,  Reason=%s  WHERE Employee_id=%s"
                          cursor.execute(update_sql, ( Start_date, End_date, No_of_Days,Reason, employee_id))
                          connection.commit()
                          print("updated the leave request data")
                          html = render_template_string(
                                                  """
                                                  <p>Your request_id: <strong>{{ Request_id }}</strong></p>
                                                  <p>Team Lead: <strong>{{ person_name }}</strong></p>
                                                  
                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name, _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(Req_Id),
                                                 person_name=Team_lead,
                                                 
                                                 )
                          msg_team_lead = Message(
                                        'Leave Request',
                          sender='enerziff@gmail.com',
                          recipients=[Team_lead_email]
                           )
                          msg_team_lead.body = "You have got a leave request  for Work From Home from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                          msg_team_lead.html = html
                          try:
                              mail.send(msg_team_lead)
                              print("mail sent to team_lead")
                          except Exception as e:
                              print("WFH update team lead email error:", e)

                    # Send email to manager
                          html = render_template_string(
                                                  """
                                                  <p>Your request_id: <strong>{{ Request_id }}</strong></p>
                                                  <p>Manager: <strong>{{person_name}}</strong></p>
                                                  <p>
                                                  <a href="{{ url_for('accept_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                                  <a href="{{ url_for('reject_request', request_id=Request_id,person_name=person_name,  _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                                  </p>

                                                  """,
                                                 Request_id=str(request_id),
                                                 person_name=Manager_name,
                                                 
                                                 )
                          msg_manager = Message(
                            'Leave Request',
                            sender='enerziff@gmail.com',
                            recipients=[Manager_email]
                            )
                          msg_manager.body = "You have got a leave request  for Work From Home from " + employee_name + " Leave dates are from " +str(Start_date) + "to" +str(End_date)+ "Total_no_of_days are.." +str(No_of_Days)+ " You can accept/reject the request by using your payroll management account."
                          msg_manager.html = html
                          try:
                              mail.send(msg_manager)
                              print("mail sent to manager")
                          except Exception as e:
                              print("WFH update manager email error:", e)

                        response={'status':"success",'From_date':Start_date,'To_date':End_date,'Applied_on':Applied_On,'clock_in_time':clock_in_time_str,}
                        return jsonify(response)

            else:
              print("request type is invalid.....")


#........................................................Accept WorkFromHome....................................................
@app.route('/accept_work_from_home/',methods=['POST','GET'])
def Accept_WFH():
    print("...................................")
    if request.method=='POST':
        Data = request.get_json()
        # Employee_Id=Data['employee_id']
        print(Data)  
        with connection.cursor() as cursor:
          Select_Query = 'SELECT Request_id,Employee_id,Employee_Name,Applied_on,Start_Date,End_Date,No_of_Days,Reason FROM Work_From_Home WHERE Status=%s'
          cursor.execute(Select_Query, ("Waiting",))
          WHF_Info=cursor.fetchall()
          print("mydata is",WHF_Info)       
          if WHF_Info:
            Response_Data={'status':'Success','WHF_Info':WHF_Info}
            return jsonify(Response_Data)
          else:
             print("requested data not availabel in database.....")
             Response_Data={'status':'Success','WHF_Info':'data not available'}
             return jsonify(Response_Data)
    


@app.route('/get_employee_WFH_Info',methods=['POST'])
def employee_WFH_data():
    if request.method=='POST':
        Data = request.get_json()
        Employee_Id=Data['employee_id']
        print(Data)
        try:
             if Data:       
               with connection.cursor() as cursor: 
                Select_Query = 'SELECT Request_id,Employee_Id,Employee_Name,Applied_on,Start_Date,End_Date,No_of_Days,Reason,Status FROM Work_From_Home WHERE Employee_Id=%s'
                cursor.execute(Select_Query,(Employee_Id,))
                Emp_WHF_Info=cursor.fetchall()
                #fetching employee count......
                Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                cursor.execute(Count_Query)
                Employee_Count=cursor.fetchall()
                 #selecting all employee_ids and names
                Select_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                cursor.execute(Select_Query)  
                Emp_Info = cursor.fetchall()
                print(Emp_WHF_Info)
                print(Employee_Count)
                print(Emp_Info)
                for i in range(len(Emp_WHF_Info)):
                    Applied_on=str(Emp_WHF_Info[i]['Applied_on'])
                    Start_Date=str(Emp_WHF_Info[i]['Start_Date'])
                    End_Date=str(Emp_WHF_Info[i]['End_Date'])
                    Emp_WHF_Info[i]['Applied_on']=Applied_on
                    Emp_WHF_Info[i]['Start_Date']=Start_Date
                    Emp_WHF_Info[i]['End_Date']=End_Date    
                Response_Data={'status':'Success','employee_Emp_WHF_Info':Emp_WHF_Info,'Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
                return jsonify(Response_Data)
             else:
                  Response_Data={'status':'failed','message':'requested_employee not there in records...','Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
                  return jsonify(Response_Data)
        except Exception as e:
            print("exception is",e)
            Response_Data={'status':'failed','message':'exception occured..'}
            return jsonify(Response_Data)


@app.route('/get_employee_status_Info',methods=['POST'])
def employee_status_info():
    print(".................................................")
    if request.method=='POST':
        Data = request.get_json()
        Employee_Id=Data['employee_id']
        print(Data)
        if Data:       
              with connection.cursor() as cursor:
                Select_Query = 'SELECT Date,Employee_id,Employee_Name,Status_Update,Issues,Completed_Task,Feature_Targets FROM Daily_Status_Update WHERE Employee_Id=%s'
                cursor.execute(Select_Query,(Employee_Id,))
                Emp_Status_Info=cursor.fetchall()
                #fetching employee count......
                Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
                cursor.execute(Count_Query)
                Employee_Count=cursor.fetchall()
                 #selecting all employee_ids and names
                Select_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
                cursor.execute(Select_Query)  
                Emp_Info = cursor.fetchall()
                print(Emp_Status_Info)
                print(Employee_Count)
                print(Emp_Info) 
                       
                Response_Data={'status':'Success','employee_Emp_Status_Info':Emp_Status_Info,'Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
                return jsonify(Response_Data)
        else:
                  Response_Data={'status':'failed','message':'requested_employee not there in records...','Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
                  return jsonify(Response_Data)


#update action_status........WFH......................
@app.route('/update_work_from_home', methods=['POST','GET'])
@app.route('/update_work_from_home/', methods=['POST','GET'])
def Update_WFH():
    print("work from home action status calling......................")
    if request.method != 'POST':
        return jsonify({'status': 'failed', 'Message': 'Only POST allowed'})
    Data = request.get_json()
    Action_Status = Data['Action_Status']
    Request_Id = str(Data['request_id'])  # keep ID as-is, no zero-padding

    # convert frontend action to DB status
    if Action_Status.lower() == "accept":
        Action_Status = "Accepted"
    elif Action_Status.lower() == "reject":
        Action_Status = "Rejected"
    print(Data)
    try:
        with connection.cursor() as cursor:
            Update_Query = 'UPDATE Work_From_Home SET Status=%s WHERE Request_id=%s'
            cursor.execute(Update_Query, (Action_Status, Request_Id))
            connection.commit()
        with connection.cursor() as cursor:
            # Return ALL WFH records after update so admin page refreshes fully
            cursor.execute(
                'SELECT Request_id,Employee_id,Employee_Name,Applied_on,'
                'Start_Date,End_Date,No_of_Days,Reason,Status '
                'FROM Work_From_Home ORDER BY Applied_on DESC'
            )
            Emp_WHF_Info = cursor.fetchall()
            # Convert dates
            for w in Emp_WHF_Info:
                for f in ('Applied_on','Start_Date','End_Date'):
                    if w.get(f) and hasattr(w[f],'strftime'):
                        w[f] = w[f].strftime('%Y-%m-%d')
                    elif w.get(f):
                        w[f] = str(w[f])
            cursor.execute('SELECT COUNT(Employee_id) FROM employee_complete_details')
            Employee_Count = cursor.fetchall()
            cursor.execute('SELECT Employee_id,Employee_Name FROM employee_complete_details')
            Emp_Info = cursor.fetchall()
        Response_Data = {'status': 'Success', 'Message': 'Status updated', 'Work_From_Home_Info': Emp_WHF_Info, 'Total_employees': Employee_Count, 'all_employee_name_id': Emp_Info}
        return jsonify(Response_Data)
    except Exception as e:
        print("exception occurred in Update_WFH:", e)
        return jsonify({'status': 'failed', 'Message': str(e), 'Work_From_Home_Info': [], 'Total_employees': [], 'all_employee_name_id': []})

#..............................WFH Accept ...........................................   
@app.route('/WFH_accept/<request_id>/<person_name>',methods=['POST','GET'])
def accept_WFH(request_id,person_name):
    print("this is work from home accept function")
    print("getting person name",request_id,person_name)
    # request_id=request_id.strip()
    Request_Id=str(request_id)
    try:
        with connection.cursor() as cursor:
          Update_Query = 'UPDATE Work_From_Home SET Status=%s WHERE Request_id=%s'
          cursor.execute(Update_Query,("Accepted",Request_Id))
          connection.commit()
        with connection.cursor() as cursor:
          Select_Query = 'SELECT Request_id,Employee_id,Employee_Name, Applied_on,Start_Date,End_Date,No_of_Days,Reason FROM Work_From_Home WHERE Status=%s '
          cursor.execute(Select_Query, ('Waiting',))
          Emp_WHF_Info=cursor.fetchall()
          Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
          cursor.execute(Count_Query)
          Employee_Count=cursor.fetchall()
                 #selecting all employee_ids and names
          Select_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
          cursor.execute(Select_Query)  
          Emp_Info = cursor.fetchall()
          Response_Data={'status':'Success','Message':'Status_Action updated successfully','Work_From_Home_Info':Emp_WHF_Info,'Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
          return jsonify(Response_Data)          
    except Exception as e:  
        Emp_WHF_Info=""
        print("exception occered in Update_WFH:",e)
        Response_Data={'status':'failed','Message':'Status_Action not updated successfully','Work_From_Home_Info':Emp_WHF_Info,'Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
        return jsonify(Response_Data) 



#.........................WFH Reject ......................................
@app.route('/WFH_Reject/<request_id>/<person_name>',methods=['POST','GET'])
def Reject_WFH(request_id,person_name):
    print("this is work from home reject function")
    print("getting person name",request_id,person_name)
    # request_id=request_id.strip()
    Request_Id=str(request_id)
    try:
        with connection.cursor() as cursor:
            Update_Query = 'UPDATE Work_From_Home SET Status=%s WHERE Request_id=%s'
            cursor.execute(Update_Query, ("Rejected", Request_Id))
            connection.commit()
        with connection.cursor() as cursor:
          Select_Query = 'SELECT Request_id,Employee_id,Employee_Name, Applied_on,Start_Date,End_Date,No_of_Days,Reason FROM Work_From_Home WHERE Status=%s '
          cursor.execute(Select_Query, ('Waiting',))
          Emp_WHF_Info=cursor.fetchall()
          Count_Query='SELECT COUNT(Employee_id) FROM employee_complete_details'
          cursor.execute(Count_Query)
          Employee_Count=cursor.fetchall()
                 #selecting all employee_ids and names
          Select_Query="SELECT Employee_id,Employee_Name FROM employee_complete_details"
          cursor.execute(Select_Query)  
          Emp_Info = cursor.fetchall()
          Response_Data={'status':'Success','Message':'Status_Action updated successfully','Work_From_Home_Info':Emp_WHF_Info,'Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
          return jsonify(Response_Data)         
    except Exception as e:  
        Emp_WHF_Info=""
        print("exception occered in Update_WFH:",e)
        Response_Data={'status':'failed','Message':'Status_Action not updated successfully','Work_From_Home_Info':Emp_WHF_Info,'Total_employees':Employee_Count,'all_employee_name_id':Emp_Info}
        return jsonify(Response_Data) 


#...........................................................MyTeamInfo..............................................................
#getting id and sending employee_leave balance info based on id .......
@app.route('/Myteam_info',methods=['POST'])
def Fetch_MyTeam_Info():
    if request.method=='POST':
        Data = request.get_json()
        Team_lead_email=Data['Team_lead_email']
        print(Data)       
        #selecting leaves from leave balance based on the employee_id.........
        with connection.cursor() as cursor: 
         try:
           #selecting fwestival info from holiday table.... 
           Select_Query='SELECT Employee_Name,Position FROM employee_complete_details where Team_lead_email = %s'
           cursor.execute(Select_Query,(Team_lead_email,))
           MyTeam_Info=cursor.fetchall()
           print("Fest_Info",MyTeam_Info)
           Response_Data = {'status':'Success','MyTeam_Info':MyTeam_Info,}
           return jsonify(Response_Data) 
         except Exception as e:
            print("exception is",e)
            Response_Data={'status':'failed','message':'data not found'}
            return jsonify(Response_Data)
    else:
        print("method not found")
        return "method not found"

@app.route('/get_employees_count', methods=['POST'])
def get_employees_count():
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:

            cursor.execute('SELECT COUNT(Employee_id) FROM employee_complete_details')
            Employee_Count = cursor.fetchall()

            cursor.execute('''
            SELECT 
            Employee_id,
            Employee_Name,
            Team_lead,
            Manager_name
            FROM employee_complete_details
            ''')
            Emp_Info = cursor.fetchall()

            # Fetch ALL WFH records (all statuses) for admin overview
            cursor.execute('''
            SELECT Request_id, Employee_id, Employee_Name,
                   Applied_on, Start_Date, End_Date, No_of_Days,
                   Reason, Status
            FROM Work_From_Home
            ORDER BY Applied_on DESC
            ''')
            Work_From_Home_Info = cursor.fetchall()

            # Fetch only Waiting ones separately for dashboard pending count
            cursor.execute('''
            SELECT COUNT(*) AS cnt FROM Work_From_Home WHERE Status=%s
            ''', ("Waiting",))
            pending_wfh_count = cursor.fetchone().get('cnt', 0)

        # Convert date objects to strings for JSON serialisation
        for w in Work_From_Home_Info:
            for f in ('Applied_on', 'Start_Date', 'End_Date'):
                if w.get(f) and hasattr(w[f], 'strftime'):
                    w[f] = w[f].strftime('%Y-%m-%d')
                elif w.get(f):
                    w[f] = str(w[f])

        return jsonify({
            "status": "Success",
            "Total_employees": Employee_Count,
            "all_employee_name_id": Emp_Info,
            "Work_From_Home_Info": Work_From_Home_Info,
            "pending_wfh_count":   pending_wfh_count
        })

    except Exception as e:
        print("ERROR in get_employees_count:", e)
        return jsonify({
            "status": "failed",
            "message": str(e),
            "Total_employees": [],
            "all_employee_name_id": [],
            "Work_From_Home_Info": []
        })

@app.route('/Clock_Adjust',methods=['POST'])
def Clock_Adjustment():
  if request.method=='POST':
    Data=request.get_json()
    Employee_Id=Data['id']
    Employee_Name=Data['username']
    Request_Type=Data['Request_Type']
    current_date= datetime.now().strftime('%Y-%m-%d')

    if Data['Request_Type']=='Attendance':
      Clock_In=Data['Clock_In']
      Clock_Out=Data['Clock_Out']
      Selected_Date=Data['Selected_Date']
      Reason=Data['Reason']
      with connection.cursor() as cursor:
        Insert_Query="INSERT INTO ClockAdjustment(Employee_id, Employee_Name,Request_Type, Clock_In, Clock_Out,Reason,Selected_Date,Inserting_Date,Request_Status) VALUES (%s, %s, %s, %s,%s,%s,%s,%s,%s)"
        cursor.execute(Insert_Query, (Employee_Id, Employee_Name,"Attendance", Clock_In,Clock_Out,Reason,Selected_Date,current_date,"waiting"))
        connection.commit()
    elif Data['Request_Type']=='Partial':
      print(".............")
      Selected_Date=Data['Selected_Date']
      Reason=Data['Reason']
      Time_of_Day=Data['Time_of_Day']
      print("time of day..",Time_of_Day,Reason,Selected_Date)
      with connection.cursor() as cursor:
        Insert_Query="INSERT INTO ClockAdjustment(Employee_id, Employee_Name,Request_Type,Reason,Time_of_Day,Selected_Date,Inserting_Date,Request_Status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(Insert_Query, (Employee_Id, Employee_Name,"Partial",Reason,Time_of_Day,Selected_Date,current_date,"waiting"))
        connection.commit() 
    elif Data['Request_Type']=='Wfh':
      Selected_Date=Data['Selected_Date']
      Reason=Data['Reason']
      with connection.cursor() as cursor:
        Insert_Query="INSERT INTO ClockAdjustment(Employee_id, Employee_Name,Request_Type,Reason,Selected_Date,Inserting_Date,Request_Status) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(Insert_Query, (Employee_Id, Employee_Name,"Wfh",Reason,Selected_Date,current_date,"waiting"))
        connection.commit() 
    elif Data['Request_Type']=='Leave':
      Selected_Date=Data['Selected_Date']
      print("..........",Selected_Date)
      Reason=Data['Reason']
      with connection.cursor() as cursor:
        Insert_Query="INSERT INTO ClockAdjustment(Employee_id, Employee_Name,Request_Type,Reason,Selected_Date,Inserting_Date,Request_Status) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(Insert_Query, (Employee_Id, Employee_Name,"Leave",Reason,Selected_Date,current_date,"waiting"))
        connection.commit()
    with connection.cursor() as cursor:                       
      Select_Query = "SELECT Team_lead_email,Manager_email,Team_lead,Manager_name FROM  employee_complete_details  WHERE Employee_id = %s AND Employee_Name = %s "
      cursor.execute(Select_Query , (Employee_Id,Employee_Name))  
      Fetch_Info= cursor.fetchone()
      print("employee data",Fetch_Info)
      Team_lead_email=Fetch_Info['Team_lead_email']
      Manager_email=Fetch_Info['Manager_email']
      Team_lead=Fetch_Info['Team_lead']
      Manager_name=Fetch_Info['Manager_name']
      print("team lead emails",Team_lead_email,Manager_email) 
      html = render_template_string(
                                                  """
                                                  <p>Dear {{ team_lead }},</p>
                                                  <p>I hope this message finds you well. I am writing to formally request for Clock Adjustments:</p>
                                                  <p>Selected Date for Clock Adjustment:<strong>{{Selected_Date}}</strong></p>                                          
                                                  <p>Reason for Clock Adjustment: <strong>{{ Reason }}</strong></p>                                                 
                                                  <p><strong>Your support and understanding are invaluable to me. Thank you for your time and consideration.</strong></p>
                                                  <p>Best regards,</p>
                                                  <p>{{ Employee_Name }}</p>                                                  
                                                   <p>
                                        <a href="{{ url_for('accept_ClockAdj_request',Employee_Id=Employee_Id,Request_Type=Request_Type,Selected_Date=Selected_Date,person_name=person_name,Employee_Name=Employee_Name, _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                        <a href="{{ url_for('reject_ClockAdj_request',Employee_Id=Employee_Id,Request_Type=Request_Type,Selected_Date=Selected_Date,person_name=person_name,Employee_Name=Employee_Name, _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                      </p>

                                                  """,
                                                
                                                 person_name=Team_lead,
                                                 team_lead=Team_lead,
                                                 Reason=Reason,
                                                 Selected_Date=Selected_Date,
                                                 Employee_Name=Employee_Name,
                                                 Request_Type=Request_Type,
                                                 Employee_Id=Employee_Id

                                                 
                                                 )
      msg_team_lead = Message(
                                    'Clock Adjustment Request',
                    sender='enerziff@gmail.com',
                    recipients=[Team_lead_email]
                    )
      msg_team_lead.body = "You have got a Clock Adjustment Request from " + Employee_Name + "."
      msg_team_lead.html = html
      mail.send(msg_team_lead)
      print("mail sent to team_lead")

      # Send email to manager
      html = render_template_string(
                                    """
                                      <p>Dear {{ Manager_name }},</p>
                                      <p>I hope this message finds you well. I am writing to formally request for Clock Adjustments:</p>
                                      <p>Clock_In: <strong>{{ Clock_In }}</strong></p>
                                      <p>Clock_Out: <strong>{{ Clock_Out }}</strong></p>
                                      <p>Selected Date for Clock Adjustment:<strong>{{Selected_Date}}</strong></p>                                          
                                      <p>Reason for Clock Adjustment: <strong>{{ Reason }}</strong></p>                                                 
                                      <p><strong>Your support and understanding are invaluable to me. Thank you for your time and consideration.</strong></p>
                                      <p>Best regards,</p>
                                      <p>{{ Employee_Name }}</p>                                                  
                                      <p>
                                        <a href="{{ url_for('accept_ClockAdj_request',Employee_Id=Employee_Id,Request_Type=Request_Type,Selected_Date=Selected_Date,person_name=person_name,Employee_Name=Employee_Name, _external=True) }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Accept</a>
                                        <a href="{{ url_for('reject_ClockAdj_request',Employee_Id=Employee_Id,Request_Type=Request_Type,Selected_Date=Selected_Date,person_name=person_name,Employee_Name=Employee_Name, _external=True) }}" style="background-color: #f44336; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reject</a>
                                      </p>
 
                                      """,
                                    
                                    person_name=Manager_name,
                                    Manager_name=Manager_name,
                                   
                                    Reason=Reason,
                                    Selected_Date=Selected_Date,
                                    Employee_Name=Employee_Name,
                                    Request_Type=Request_Type,
                                    Employee_Id=Employee_Id

                                    
                                    )
      msg_manager = Message(
      'Leave Request',
      sender='enerziff@gmail.com',
      recipients=[Manager_email]
      )
      msg_manager.body = "You have got a Clock Adjustment Request from " + Employee_Name + "."
      msg_manager.html = html
      mail.send(msg_manager)
      print("mail sent to manager")
      response={'status':"success","message":"mails sent successfully"}
  return jsonify(response)


@app.route('/Get_ClockAdj',methods=['POST'])
def Fetch_Get_ClockAdj_Info():
    if request.method=='POST':
        Data = request.get_json()
        print(Data) 
        Selected_Date=Data['Selected_Date'] 
        Employee_id=Data['user_id']
        print("...........type",type(Selected_Date))
        #selecting leaves from leave balance based on the employee_id.........
        with connection.cursor() as cursor: 
         try:
           print("..............................")
           Input_Date = datetime.strptime(Selected_Date, "%Y-%m-%d")
           print("type........", type(Input_Date), Input_Date)            
# Convert the datetime object to the desired format
           Formatted_Date = Input_Date.strftime("%a, %d %b %Y %H:%M:%S %Z")
           #selecting festival info from holiday table.... 
           Select_Query='SELECT Date,clock_in_time,clock_out_time,Avg_working_hrs FROM Employee_Attendance_Data WHERE Date=%s And Employee_id=%s'
           cursor.execute(Select_Query, (Input_Date, Employee_id))
           Clock_Info=cursor.fetchall()
           print("Clock_Info",Clock_Info)
           print("..............................")
           for i in range(len(Clock_Info)):
            Clock_In_Time=str(Clock_Info[i]['clock_in_time'])
            Clock_Out_Time=str(Clock_Info[i]['clock_out_time'])
            Avg_Working_Hrs=str(Clock_Info[i]['Avg_working_hrs'])
            Clock_Info[i]['clock_in_time']=Clock_In_Time
            Clock_Info[i]['clock_out_time']=Clock_Out_Time
            Clock_Info[i]['Avg_working_hrs']=Avg_Working_Hrs

           Response_Data = {'status':'Success','Clock_Info':Clock_Info,}
           return jsonify(Response_Data) 
         except Exception as e:
            print("exception is",e)
            Response_Data={'status':'failed','message':'data not found'}
            return jsonify(Response_Data)
    else:
        print("method not found")
        return "method not found"


#........................................................AcceptLeaveRequest....................................................
@app.route('/accept_req/<Employee_Id>/<Request_Type>/<Selected_Date>/<person_name>/<Employee_Name>',methods=['POST','GET'])
def accept_ClockAdj_request(Employee_Id,Selected_Date,Request_Type,person_name,Employee_Name):
  try:
    print("getting person name and Request type",Request_Type,Selected_Date,person_name,Employee_Id,Employee_Name)
    with connection.cursor() as cursor:
     update_sql = "UPDATE ClockAdjustment SET Request_Status=%s where Employee_id=%s AND Selected_Date=%s"
     cursor.execute(update_sql,("Accepted", Employee_Id, Selected_Date))
     connection.commit()
    if Request_Type=="Attendance":
      with connection.cursor() as cursor:
        Select_Query='SELECT Clock_In,Clock_Out FROM ClockAdjustment WHERE Employee_id=%s AND Selected_Date=%s'
        cursor.execute(Select_Query, (Employee_Id,Selected_Date))
        ClockAdjustment_Info=cursor.fetchone()
        print("Clock_Info",ClockAdjustment_Info)
        Clock_In=ClockAdjustment_Info['Clock_In']
        Clock_Out=ClockAdjustment_Info['Clock_Out']
        print(Clock_In,Clock_Out)
        Avg_Working_Hrs=Clock_Out-Clock_In
        print(Avg_Working_Hrs)
        Update_Query = "UPDATE Employee_Attendance_Data SET clock_in_time=%s,clock_out_time = %s,Avg_working_hrs= %s WHERE employee_id = %s AND Date= %s"
        cursor.execute(Update_Query,(Clock_In, Clock_Out,Avg_Working_Hrs,Employee_Id,Selected_Date))
        connection.commit()
    elif Request_Type=="Wfh":
      with connection.cursor() as cursor:
        Update_Query = "UPDATE Employee_Attendance_Data SET clock_in_time=%s,clock_out_time = %s,Avg_working_hrs= %s WHERE employee_id = %s AND Date= %s"
        cursor.execute(Update_Query,("09:30:00","17:30:00","08:00:00",Employee_Id,Selected_Date))
        connection.commit()
    elif Request_Type=="Partial":
       with connection.cursor() as cursor:
        Select_Query='SELECT Time_of_Day FROM ClockAdjustment WHERE Employee_id=%s AND Selected_Date=%s'
        cursor.execute(Select_Query, (Employee_Id,Selected_Date))
        ClockAdjustment_Info=cursor.fetchone()
        print("clock_info",ClockAdjustment_Info)
        Time_of_Day=ClockAdjustment_Info['Time_of_Day']
        print(Time_of_Day)
        if Time_of_Day=="Forenoon": 
          Update_Query = "UPDATE Employee_Attendance_Data SET clock_in_time=%s,clock_out_time = %s,Avg_working_hrs= %s WHERE employee_id = %s AND Date= %s"
          cursor.execute(Update_Query,("14:00:00","17:30:00","03:30:00",Employee_Id,Selected_Date))
          connection.commit()   
        elif Time_of_Day=="Afternoon": 
          with connection.cursor() as cursor:
            Update_Query = "UPDATE Employee_Attendance_Data SET clock_in_time=%s,clock_out_time = %s,Avg_working_hrs= %s WHERE employee_id = %s AND Date= %s"
            cursor.execute(Update_Query,("09:30:00","13:00:00","03:30:00",Employee_Id,Selected_Date))
            connection.commit()
    elif Request_Type=="Leave":
      with connection.cursor() as cursor:
        Update_Query = "UPDATE Employee_Attendance_Data SET clock_in_time=%s,clock_out_time = %s,Avg_working_hrs= %s WHERE employee_id = %s AND Date= %s"
        cursor.execute(Update_Query,("09:30:00","17:30:00","08:00:00",Employee_Id,Selected_Date))
        connection.commit()
      with connection.cursor() as cursor:
        Select_Query='SELECT Sick_Leave,No_of_leaves,Pending_leaves,Taken_leaves FROM Leave_balance where Employee_id=%s'
        cursor.execute(Select_Query, (Employee_Id))
        Leave_Bal_Info=cursor.fetchone()
        print("Leave_Bal_Info",Leave_Bal_Info)
        Sick_Leave =Leave_Bal_Info['Sick_Leave']
        No_of_leaves=Leave_Bal_Info['No_of_leaves']
        Pending_leaves=Leave_Bal_Info['Pending_leaves']
        Taken_leaves=Leave_Bal_Info['Taken_leaves']
        Sick_Leave=Sick_Leave-1
        Taken_leaves=No_of_leaves+1
        Pending_leaves=No_of_leaves-Taken_leaves
        Update_Query = "UPDATE Leave_balance SET Sick_Leave=%s,No_of_leaves = %s,Pending_leaves=%s,Taken_leaves=%s WHERE employee_id=%s"
        cursor.execute(Update_Query,(Sick_Leave,No_of_leaves,Pending_leaves,Taken_leaves,Employee_Id))
        connection.commit()
      with connection.cursor() as cursor:
        Select_Query='SELECT Employee_Name,Reason FROM ClockAdjustment WHERE Employee_id=%s AND Selected_Date=%s'
        cursor.execute(Select_Query, (Employee_Id,Selected_Date))
        ClockAdjustment_Info=cursor.fetchone()
        print("Reason",ClockAdjustment_Info)
        Reason=ClockAdjustment_Info['Reason']
        Insert_Query="INSERT INTO Leave_history(Request_id,Employee_id, Employee_Name,Start_date,End_date,No_of_Days,Leave_Type,Approved_By_Whom,Add_Employees,Reason,Status,Team_lead,Manager_name,Team_lead_email,Manager_email) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(Insert_Query, ("None",Employee_Id,Employee_Name,Selected_Date,Selected_Date,"1","Sick_Leave",person_name,"NONE",Reason,"Approved",person_name,"NONE","None","None"))
        connection.commit()
    with connection.cursor() as cursor:
     Select_Query='SELECT Employee_email FROM employee_complete_details WHERE Employee_id=%s'
     cursor.execute(Select_Query, (Employee_Id))
     Emp_Email_Info=cursor.fetchone()  
    print("Employee email:", Emp_Email_Info['Employee_email'])
    Emp_Email= Emp_Email_Info['Employee_email']
    msg = Message(
                'Clock Adjustment Request Status ',
                sender='enerziff@gmail.com',
                recipients=[Emp_Email]
                )
    msg.body = "Your Clock Adjustment Request Accepted"
    mail.send(msg)
    print("status mail sent to employee",Emp_Email)  
    return 'Clock Adjustment Request is accepted for '+Employee_Id+". Thank You!"                     
  except Exception as e:
    print("exception occuring",(e)) 
    return 'Clock Adjustment Request is accepted for '+Employee_Id+". Thank You!"                     


      
@app.route('/reject_req/<Employee_Id>/<Selected_Date>/<Request_Type>/<person_name>',methods=['POST','GET'])
def reject_ClockAdj_request(Employee_Id,Selected_Date,Request_Type,person_name):
  try:
    print("getting person name and Request type",Request_Type,Selected_Date,person_name,Employee_Id)
    with connection.cursor() as cursor:
     update_sql = "UPDATE ClockAdjustment SET Request_Status=%s where Employee_id=%s AND Selected_Date=%s"
     cursor.execute(update_sql,("Rejected", Employee_Id, Selected_Date))
     connection.commit() 
    with connection.cursor() as cursor:
     Select_Query='SELECT Employee_email FROM employee_complete_details WHERE Employee_id=%s'
     cursor.execute(Select_Query, (Employee_Id))
     Emp_Email=cursor.fetchone()  
    print("Employee email:", Emp_Email)
    msg = Message(
                'Clock Adjustment Request Status ',
                sender='enerziff@gmail.com',
                recipients=[Emp_Email]
                )
    msg.body = "Your Clock Adjustment Request Rejected"
    mail.send(msg)
    print("status mail sent")                       
  except Exception as e:
    print("exception occuring",(e)) 
  return 'Clock Adjustment Request is Rejected for '+Employee_Id+". Thank You!"


@app.route('/profile', methods=['POST'])
def Fetch_Profile_Info():

    Data = request.get_json()
    print("Received Data:", Data)

    employee_id = Data.get("employee_id")

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:

            Select_Query = """
            SELECT Employee_Name,
                   Username,
                   Employee_id,
                   Employee_email,
                   Phone_Number,
                   Department,
                   Position,
                   Gender,
                   Address,
                   Skills,
                   Team_lead,
                   Team_lead_email,
                   Manager_name,
                   Manager_email,
                   Work_location
            FROM employee_complete_details
            WHERE Employee_id = %s
            """

            cursor.execute(Select_Query, (employee_id,))
            Profile_Info = cursor.fetchone()

            print("Profile_Info:", Profile_Info)

            return jsonify({
                "status": "success",
                "Profile_Info": Profile_Info
            })

    except Exception as e:
        print("Exception:", e)

        return jsonify({
            "status": "failed",
            "message": "data not found"
        })
    

@app.route('/Announcement',methods=['POST'])
def Fetch_Announcement():
    if request.method=='POST':
        Data = request.get_json()
        Slected_Date=Data['Selected_Date']
        print(Data)       
        #selecting leaves from leave balance based on the employee_id.........
        with connection.cursor() as cursor: 
         try:
           #selecting fwestival info from holiday table.... 
           Select_Query='SELECT * FROM Announcement WHERE Announcement_date=%s'
           cursor.execute(Select_Query,(Slected_Date))
           Announcement_Info=cursor.fetchall()
           print("Announcement_Info",Announcement_Info)
           Response_Data = {'status':'Success','Announcement_Info':Announcement_Info,}
           return jsonify(Response_Data) 
         except Exception as e:
            print("exception is",e)
            Response_Data={'status':'failed','message':'data not found'}
            return jsonify(Response_Data)
    else:
        print("method not found")
        return "method not found"

@app.route('/Anounce_Data', methods=['POST'])
def Anounce_Data():
  print("this is announce data")
  if request.method=='POST':
    Data=request.get_json()
    Selected_Date=Data['Selected_Date']
    print(Selected_Date)
    Emp_Id=Data['employeeid']
    Current_Date=datetime.now().date()
    Current_Formate_Date=datetime.now().strftime("%Y-%m-%d")
    No_Of_Days=30
    New_Date_Str=Current_Date+timedelta(No_Of_Days)
    New_Date=New_Date_Str.strftime("%Y-%m-%d")
    with connection.cursor() as cursor:
      Announcement_Query='SELECT Employee_Name,Announcement,Announcement_date FROM Announcement WHERE Announcement_date=%s AND Employee_id=%s'
      cursor.execute(Announcement_Query,(Selected_Date,Emp_Id))
      Announcement_Info=cursor.fetchall()
      print("this is data",Announcement_Info)
      Response_Data={'status':'success',"Announcement_Info":Announcement_Info}
    return jsonify(Response_Data)
  else:
    Announcement_Info=""
    Response_Data={'status':'failed',"Announcement_Info":Announcement_Info}
    return jsonify(Response_Data)


@app.route('/Announcement_Update',methods=['POST'])
def Announcement_Update():
    if request.method=='POST':
        Data = request.get_json()
        print("This is Announcement_Update",Data)   
        Employee_Id=Data['employeeid']  
        user_type=Data['user_type'] 
        Announcement=Data['Selected_Announcement']
        Selected_Date=Data['date']

        # if user_type in ['Employer', 'Employee']:
        # if user_type == 'Employer':
        try:
          if user_type == 'Employer':
            with connection.cursor() as cursor: 
              Update_Query = 'UPDATE Announcement SET Announcement=%s WHERE Announcement_date=%s'
              cursor.execute(Update_Query,(Announcement,Selected_Date))
              updated_info=cursor.fetchall()
              print("updated information in Announcement_Update",updated_info)   
              connection.commit()
          else:
            with connection.cursor() as cursor: 
              Update_Query = 'UPDATE Announcement SET Announcement=%s WHERE Announcement_date=%s AND Employee_id=%s'
              cursor.execute(Update_Query,(Announcement,Selected_Date, Employee_Id))
              updated_info=cursor.fetchall()
              print("updated information in Announcement_Update",updated_info)   
              connection.commit()
            
          with connection.cursor() as cursor:
            Current_Date = datetime.now().date()
            Current_Formate_Date= datetime.now().strftime('%Y-%m-%d')
            No_Of_Days=30
            New_Date_Str = Current_Date + timedelta(No_Of_Days)
            New_Date= New_Date_Str.strftime('%Y-%m-%d')
            print("Current Formatted Date:", Current_Formate_Date)
            print("New Date:", New_Date)
            Select_Query='SELECT Employee_Name, Announcement,Announcement_date FROM Announcement WHERE Announcement_date >= %s'
            cursor.execute(Select_Query,(Current_Date,))
            Announcement_Info=cursor.fetchall()
            print("Announcement_Info",Announcement_Info)   
            Response_Data = {'status':'Success','Announcement_Info':Announcement_Info}
            return jsonify(Response_Data) 
        except Exception as e:
          print("exception is",e)
          Response_Data={'status':'failed','message':'data not found'}
          return jsonify(Response_Data)
    else:
        print("method not found")
        return "method not found"


@app.route('/notification', methods=['POST'])
def notification():
  print("notification is app.py")
  Data=request.get_json()
  user_id = Data.get('user_id')
  print(user_id)
  username=Data.get('username')
  print("username", username)
  print("Received data:", Data)
  Current_Date = datetime.now().date()
  Current_Formate_Date= datetime.now().strftime('%Y-%m-%d')
  print("Current_Formate_Date", Current_Formate_Date)
  Ten_Days_Ago = Current_Date - timedelta(days=10)
  Ten_Days_Ago_Formate_Date = Ten_Days_Ago.strftime('%Y-%m-%d')
  print("Ten_Days_Ago:", Ten_Days_Ago_Formate_Date)
  # Calculate the date 20 days ago
  Twenty_Days_Ago = Current_Date - timedelta(days=30)
  Twenty_Days_Ago_Formate_Date = Twenty_Days_Ago.strftime('%Y-%m-%d')
  print("Twenty_Days_Ago:", Twenty_Days_Ago_Formate_Date)
  inserting_date=Data.get('inserting_date', datetime.now().strftime('%Y-%m-%d'))
  print(f"Inserting Date: {inserting_date}")  
  No_Of_Days=30
  New_Date_Str = Current_Date + timedelta(No_Of_Days)
  New_Date= New_Date_Str.strftime('%Y-%m-%d')
  print("new_date:", New_Date)
  with connection.cursor() as cursor:
    Birthday_Query='SELECT Employee_id, Employee_Name, From_Employee_name, Wished_On, Wish FROM birthdays_of_employee WHERE Employee_Name = %s'
    cursor.execute(Birthday_Query,(username,))
    Birthday_Info=cursor.fetchall()
    print("this is insert command of notification app.py",Birthday_Info )
    Delete_Birth_Query='DELETE FROM birthdays_of_employee WHERE Wished_On BETWEEN %s AND %s '
    cursor.execute(Delete_Birth_Query,(Twenty_Days_Ago_Formate_Date, Ten_Days_Ago_Formate_Date))
    connection.commit()
    print("this is delete command of notification app.py",Birthday_Info )
    Response_Data={'status':'success',"Birthday_Info":Birthday_Info}

    # Response_Data={'status':'success',"Birthday_Info":Delete_Birthday_Info}
  return jsonify(Response_Data)




@app.route('/Birthday', methods=['POST'])
def Insert_Birthday():
  print("this is Insert_Birthday in app function ")
  if request.method=='POST':
    data=request.get_json()
    print("the Birthday data is..... ",data)
    employee_id=data.get('employee_id')
    if employee_id is None:
      return jsonify({'status': 'error', 'message': 'employee_id (userid) is required'}), 400
    employee_name=data.get('employee_name')
    wish=data.get('wish')
    inserting_date=data.get('inserting_date', datetime.now().strftime('%Y-%m-%d'))  
    username=data.get('username')
    print("username of loggedin user:", username) 
    print(f"Employee ID: {employee_id}")
    print(f"Employee Name: {employee_name}")
    print(f"Wish: {wish}")
    print(f"Inserting Date: {inserting_date}")
    with connection.cursor() as cursor:
      Insert_Query = 'INSERT INTO birthdays_of_employee (Employee_id, Employee_Name, Wished_On, Wish, From_Employee_name) VALUES(%s, %s, %s, %s, %s)'
      cursor.execute(Insert_Query,(employee_id,employee_name,inserting_date,wish,username))
      connection.commit()
      print("Data successfully inserted into Birthday table")
      Response_Data={'status':'success',"message":'Announcement data inserted into Announcement_table successfully..'}
      return jsonify(Response_Data)


@app.route('/query', methods=['POST'])
def Insert_query():

    Data = request.get_json()
    print("Received Data:", Data)

    Employee_Id = Data['Employee_id']
    Employee_Name = Data['Employee_Name']
    Employee_Email = Data.get('Employee_Email')
    Query_text = Data['Query']

    Date_now = datetime.now().strftime('%Y-%m-%d')
    Time_now = datetime.now().strftime('%H:%M:%S')

    with connection.cursor() as cursor:

        insert_query = """
            INSERT INTO doubts
            (Employee_id, Employee_Name, Employee_Email, Date, Time, Query, Status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
            """

        cursor.execute(insert_query,
                       (Employee_Id, Employee_Name,
                        Employee_Email, Date_now,
                        Time_now, Query_text))

        connection.commit()

    # Fetch updated queries
    with connection.cursor() as cursor:

        select_query = """
        SELECT query_id, Employee_id, Employee_Name,
               Employee_Email, Date, Time,
               Query, Status
        FROM doubts
        ORDER BY Date DESC, Time DESC
        """

        cursor.execute(select_query)
        Query_Info = cursor.fetchall()

    return jsonify({
        "status": "success",
        "message": "Query inserted successfully",
        "Query_Info": Query_Info
    })

@app.route('/reply_query', methods=['POST'])
def reply_query():

    data = request.get_json()

    query_id = data.get("query_id")
    answer = data.get("answer")

    with connection.cursor() as cursor:
        update_sql = """
            UPDATE doubts
            SET Status = 'Replied',
                Reply = %s
            WHERE query_id = %s
        """
        cursor.execute(update_sql, (answer, query_id))
        connection.commit()

    return jsonify({
        "status": "success",
        "message": "Reply saved"
    })


@app.route('/Queries_Info', methods=['GET','POST'])
def Queries_Info():
    Data = request.get_json()

    employee_id = Data.get("employee_id")
    request_type = Data.get("request")

    with connection.cursor() as cursor:

        # 🔵 EMPLOYER → GET ALL QUERIES
        if request_type == "all":
            query = """
                SELECT query_id, Employee_id, Employee_Name,
                       Employee_Email, Date, Time,
                       Query, Status, Reply
                FROM doubts
                ORDER BY Date DESC, Time DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()

        # 🟢 EMPLOYEE → GET ONLY THEIR QUERIES
        else:
            query = """
                SELECT query_id, Employee_id, Employee_Name,
                       Employee_Email, Date, Time,
                       Query, Status, Reply
                FROM doubts
                WHERE Employee_id = %s
                ORDER BY Date DESC, Time DESC
            """
            cursor.execute(query, (employee_id,))
            rows = cursor.fetchall()

    queries = []

    for row in rows:
        row["Date"] = str(row["Date"])
        row["Time"] = str(row["Time"])
        queries.append(row)

    return jsonify({
        "Queries_Info": queries
})
    

@app.route('/employee_queries', methods=['POST'])
def employee_queries():

    data = request.get_json()
    employee_id = data['employee_id']

    with connection.cursor() as cursor:
        sql = """
        SELECT query_id,
               Date,
               Time,
               Query,
               Status,
               Reply
        FROM doubts
        WHERE Employee_id = %s
        ORDER BY Date DESC, Time DESC
        """
        cursor.execute(sql, (employee_id,))

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))

    return jsonify({"Queries_Info": result})


@app.route('/admin_notification', methods=['POST'])
def admin_notification():
  print("notification is app.py")
  Data=request.get_json()
  user_id = Data.get('Employee_id')
  print("user_id", user_id)
  username=Data.get('Employee_Name')
  print("username", username)
  print("Received data:", Data)
  Current_Date = datetime.now().date()
  Current_Formate_Date= datetime.now().strftime('%Y-%m-%d')
  print("Current_Formate_Date", Current_Formate_Date)
  No_Of_Days=30
  New_Date_Str = Current_Date + timedelta(days=No_Of_Days)
  New_Date= New_Date_Str.strftime('%Y-%m-%d')
  print("new_date:", New_Date)
  with connection.cursor() as cursor:
    Query_Query='SELECT Employee_id,Employee_Name,Employee_Email,Date,Query FROM doubts'
    cursor.execute(Query_Query)
    Queries_Info=cursor.fetchall()
    print("this is insert command of notification app.py",Queries_Info)
    Response_Data={'status':'success',"Queries_Info":Queries_Info}
  return jsonify(Response_Data)


# ─────────────────────────────────────────────────────────────
# All leaves for ONE employee — used by employee leave status page
# Returns pending (Leave_Request) + accepted/rejected (Leave_history)
# ─────────────────────────────────────────────────────────────
@app.route('/get_employee_all_leaves', methods=['POST'])
def get_employee_all_leaves():
    try:
        Data = request.get_json()
        Employee_Id = Data.get('employee_id')
        if not Employee_Id:
            return jsonify({'status': 'error', 'message': 'employee_id required'}), 400

        with connection.cursor() as cursor:
            # Pending / Waiting
            cursor.execute(
                'SELECT Applied_on, Start_date, End_date, No_of_Days, '
                'Leave_Type, Reason, Request_id, Status '
                'FROM Leave_Request WHERE Employee_id=%s ORDER BY Applied_on DESC',
                (Employee_Id,)
            )
            pending = cursor.fetchall()

            # Accepted and Rejected — Leave_history has no Applied_on column
            cursor.execute(
                'SELECT Start_date AS Applied_on, Start_date, End_date, No_of_Days, '
                'Leave_Type, Reason, Request_id, Status, Approved_By_Whom '
                'FROM Leave_history WHERE Employee_id=%s ORDER BY Start_date DESC',
                (Employee_Id,)
            )
            history = cursor.fetchall()

        all_leaves = list(pending) + list(history)

        for lv in all_leaves:
            for f in ('Applied_on', 'Start_date', 'End_date'):
                if lv.get(f) and hasattr(lv[f], 'strftime'):
                    lv[f] = lv[f].strftime('%Y-%m-%d')
                elif lv.get(f):
                    lv[f] = str(lv[f])

        return jsonify({'status': 'success', 'all_leaves': all_leaves})

    except Exception as e:
        print("get_employee_all_leaves error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ─────────────────────────────────────────────────────────────
# All-employees leave summary used by admin analytics
# Returns every leave row from BOTH Leave_Request and Leave_history
# ─────────────────────────────────────────────────────────────
@app.route('/get_all_leaves_summary', methods=['POST'])
def get_all_leaves_summary():
    try:
        with connection.cursor() as cursor:
            # Pending leaves
            cursor.execute(
                'SELECT Employee_id, Employee_Name, Applied_on, Start_date, End_date, '
                'No_of_Days, Leave_Type, Reason, Request_id, Status FROM Leave_Request'
            )
            pending = cursor.fetchall()

            # Accepted / Rejected history — Leave_history has no Applied_on column
            cursor.execute(
                'SELECT Employee_id, Employee_Name, Start_date AS Applied_on, '
                'Start_date, End_date, No_of_Days, Leave_Type, Reason, '
                'Request_id, Status, Approved_By_Whom FROM Leave_history'
            )
            history = cursor.fetchall()

        all_leaves = list(pending) + list(history)

        # Convert any date objects to strings
        for lv in all_leaves:
            for f in ('Applied_on', 'Start_date', 'End_date'):
                if lv.get(f) and hasattr(lv[f], 'strftime'):
                    lv[f] = lv[f].strftime('%Y-%m-%d')
                elif lv.get(f):
                    lv[f] = str(lv[f])

        return jsonify({'status': 'success', 'all_leaves': all_leaves})

    except Exception as e:
        print("get_all_leaves_summary error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_all_attendance_summary', methods=['POST'])
def get_all_attendance_summary():
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    e.Employee_id,
                    e.Employee_Name,
                    COUNT(DISTINCT a.Date) AS present_days
                FROM employee_complete_details e
                LEFT JOIN Employee_Attendance_Data a
                    ON e.Employee_id = a.employee_id
                GROUP BY e.Employee_id, e.Employee_Name
                ORDER BY present_days DESC
            """)
            summary = cursor.fetchall()

            cursor.execute("""
                SELECT a.employee_id, a.employee_name, a.Date
                FROM Employee_Attendance_Data a
                ORDER BY a.Date ASC
            """)
            all_rows = cursor.fetchall()

        for row in all_rows:
            if row.get('Date') and hasattr(row['Date'], 'strftime'):
                row['Date'] = row['Date'].strftime('%Y-%m-%d')
            elif row.get('Date'):
                row['Date'] = str(row['Date'])

        return jsonify({
            'status': 'success',
            'summary': summary,
            'all_rows': all_rows
        })
    except Exception as e:
        print("get_all_attendance_summary error:", e)
        return jsonify({'status':'error','message':str(e),'summary':[],'all_rows':[]}), 500
    
# ════════════════════════════════════════════════════════════════
#  ADMIN CHATBOT FLASK ROUTES
#  Add all of these to your app.py (before the if __name__ block)
#  Tables used (from your schema):
#    Leave_balance, Leave_Request, Work_From_Home,
#    Employee_Attendance_Data, Daily_Status_Update, Announcement
# ════════════════════════════════════════════════════════════════

from datetime import date, timedelta

# ── helper ───────────────────────────────────────────────────────
def _today():      return date.today().strftime('%Y-%m-%d')
def _yesterday():  return (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
def _tomorrow():   return (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
def _n_days_ago(n): return (date.today() - timedelta(days=n)).strftime('%Y-%m-%d')


# ── 1. LEAVE BALANCE — specific employee by name ─────────────────
@app.route('/chatbot/leave_by_name', methods=['POST'])
def chatbot_leave_by_name():
    try:
        name = request.get_json().get('name', '')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Employee_Name, Sick_Leave, Wedding_Leave,
                       Maternity_Leave, Paternity_Leave,
                       No_of_leaves, Taken_leaves, Pending_leaves
                FROM Leave_balance
                WHERE Employee_Name LIKE %s
                LIMIT 1
            """, (f'%{name}%',))
            row = cursor.fetchone()
        if row:
            return jsonify({
                "status": "success",
                "employee_name": row["Employee_Name"],
                "sick_leave":      row["Sick_Leave"],
                "wedding_leave":   row["Wedding_Leave"],
                "maternity_leave": row["Maternity_Leave"],
                "paternity_leave": row["Paternity_Leave"],
                "total_leaves":    row["No_of_leaves"],
                "taken_leaves":    row["Taken_leaves"],
                "pending_leaves":  row["Pending_leaves"]
            })
        return jsonify({"status": "error", "message": "Not found"}), 404
    except Exception as e:
        print("chatbot_leave_by_name error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 2. LEAVE BALANCE — all employees ────────────────────────────
@app.route('/chatbot/all_leave_balance', methods=['POST'])
def chatbot_all_leave_balance():
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Employee_Name, No_of_leaves, Taken_leaves, Pending_leaves
                FROM Leave_balance
                ORDER BY Employee_Name
            """)
            rows = cursor.fetchall()
        return jsonify({"status": "success", "records": rows})
    except Exception as e:
        print("chatbot_all_leave_balance error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 3. ATTENDANCE — specific employee by name & day ─────────────
@app.route('/chatbot/attendance_by_name', methods=['POST'])
def chatbot_attendance_by_name():
    try:
        data = request.get_json()
        name = data.get('name', '')
        day  = data.get('day', 'current_month')

        if day == 'today':
            date_filter = "AND Date = %s"
            params = (f'%{name}%', _today())
        elif day == 'yesterday':
            date_filter = "AND Date = %s"
            params = (f'%{name}%', _yesterday())
        elif day == 'tomorrow':
            date_filter = "AND Date = %s"
            params = (f'%{name}%', _tomorrow())
        elif day.startswith('last_') and day.endswith('_days'):
            n = int(day.split('_')[1])
            date_filter = "AND Date >= %s"
            params = (f'%{name}%', _n_days_ago(n))
        else:   # current_month
            date_filter = "AND MONTH(Date) = MONTH(CURDATE()) AND YEAR(Date) = YEAR(CURDATE())"
            params = (f'%{name}%',)

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) as days_present
                FROM Employee_Attendance_Data
                WHERE employee_name LIKE %s {date_filter}
            """, params)
            row = cursor.fetchone()
        return jsonify({"status": "success", "days_present": row["days_present"] if row else 0})
    except Exception as e:
        print("chatbot_attendance_by_name error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 4. ATTENDANCE — all employees ───────────────────────────────
@app.route('/chatbot/all_attendance', methods=['POST'])
def chatbot_all_attendance():
    try:
        data = request.get_json()
        day  = data.get('day', 'current_month')

        if day == 'today':
            date_filter = "WHERE Date = %s"
            params = (_today(),)
        elif day == 'yesterday':
            date_filter = "WHERE Date = %s"
            params = (_yesterday(),)
        elif day == 'tomorrow':
            date_filter = "WHERE Date = %s"
            params = (_tomorrow(),)
        elif day.startswith('last_') and day.endswith('_days'):
            n = int(day.split('_')[1])
            date_filter = "WHERE Date >= %s"
            params = (_n_days_ago(n),)
        else:
            date_filter = "WHERE MONTH(Date) = MONTH(CURDATE()) AND YEAR(Date) = YEAR(CURDATE())"
            params = ()

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT employee_name, COUNT(*) as days
                FROM Employee_Attendance_Data
                {date_filter}
                GROUP BY employee_name
                ORDER BY employee_name
            """, params)
            rows = cursor.fetchall()
        return jsonify({"status": "success", "records": rows})
    except Exception as e:
        print("chatbot_all_attendance error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 5. WFH — specific employee ──────────────────────────────────
@app.route('/chatbot/wfh_by_name', methods=['POST'])
def chatbot_wfh_by_name():
    try:
        data = request.get_json()
        name = data.get('name', '')
        day  = data.get('day', 'all')

        if day == 'today':
            date_filter = "AND Start_Date <= %s AND End_Date >= %s"
            params = (f'%{name}%', _today(), _today())
        elif day == 'yesterday':
            date_filter = "AND Start_Date <= %s AND End_Date >= %s"
            params = (f'%{name}%', _yesterday(), _yesterday())
        elif day == 'tomorrow':
            date_filter = "AND Start_Date <= %s AND End_Date >= %s"
            params = (f'%{name}%', _tomorrow(), _tomorrow())
        elif day == 'pending':
            date_filter = "AND Status = 'Pending'"
            params = (f'%{name}%',)
        else:
            date_filter = ""
            params = (f'%{name}%',)

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) as cnt
                FROM Work_From_Home
                WHERE Employee_Name LIKE %s {date_filter}
            """, params)
            row = cursor.fetchone()
        return jsonify({"status": "success", "count": row["cnt"] if row else 0})
    except Exception as e:
        print("chatbot_wfh_by_name error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 6. WFH — all employees ──────────────────────────────────────
@app.route('/chatbot/all_wfh', methods=['POST'])
def chatbot_all_wfh():
    try:
        data = request.get_json()
        day  = data.get('day', 'all')

        if day == 'today':
            date_filter = "WHERE Start_Date <= %s AND End_Date >= %s"
            params = (_today(), _today())
        elif day == 'yesterday':
            date_filter = "WHERE Start_Date <= %s AND End_Date >= %s"
            params = (_yesterday(), _yesterday())
        elif day == 'tomorrow':
            date_filter = "WHERE Start_Date <= %s AND End_Date >= %s"
            params = (_tomorrow(), _tomorrow())
        elif day == 'pending':
            date_filter = "WHERE Status = 'Pending'"
            params = ()
        else:
            date_filter = ""
            params = ()

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT Employee_Name,
                       DATE_FORMAT(Start_Date,'%%Y-%%m-%%d') as Start_Date,
                       DATE_FORMAT(End_Date,'%%Y-%%m-%%d')   as End_Date,
                       Status
                FROM Work_From_Home
                {date_filter}
                ORDER BY Applied_on DESC
            """, params)
            rows = cursor.fetchall()
        return jsonify({"status": "success", "records": rows})
    except Exception as e:
        print("chatbot_all_wfh error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 7. LEAVE STATUS — specific employee ────────────────────────
@app.route('/chatbot/leave_by_name_day', methods=['POST'])
def chatbot_leave_by_name_day():
    try:
        data = request.get_json()
        name = data.get('name', '')
        day  = data.get('day', 'all')

        if day == 'today':
            date_filter = "AND Start_date <= %s AND End_date >= %s"
            params = (f'%{name}%', _today(), _today())
        elif day == 'yesterday':
            date_filter = "AND Start_date <= %s AND End_date >= %s"
            params = (f'%{name}%', _yesterday(), _yesterday())
        elif day == 'tomorrow':
            date_filter = "AND Start_date <= %s AND End_date >= %s"
            params = (f'%{name}%', _tomorrow(), _tomorrow())
        elif day == 'pending':
            date_filter = "AND Status = 'Pending'"
            params = (f'%{name}%',)
        else:
            date_filter = ""
            params = (f'%{name}%',)

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT Leave_Type,
                       DATE_FORMAT(Start_date,'%%Y-%%m-%%d') as Start_date,
                       DATE_FORMAT(End_date,'%%Y-%%m-%%d')   as End_date,
                       Status, No_of_Days
                FROM Leave_Request
                WHERE Employee_Name LIKE %s {date_filter}
                ORDER BY Applied_on DESC
            """, params)
            rows = cursor.fetchall()
        return jsonify({"status": "success", "records": rows})
    except Exception as e:
        print("chatbot_leave_by_name_day error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 8. DAILY STATUS — specific employee ────────────────────────
@app.route('/chatbot/status_by_name', methods=['POST'])
def chatbot_status_by_name():
    try:
        data = request.get_json()
        name = data.get('name', '')
        day  = data.get('day', 'today')

        if day == 'today':
            date_filter = "AND Date = %s"
            params = (f'%{name}%', _today())
        elif day == 'yesterday':
            date_filter = "AND Date = %s"
            params = (f'%{name}%', _yesterday())
        elif day == 'tomorrow':
            date_filter = "AND Date = %s"
            params = (f'%{name}%', _tomorrow())
        elif day.startswith('last_') and day.endswith('_days'):
            n = int(day.split('_')[1])
            date_filter = "AND Date >= %s"
            params = (f'%{name}%', _n_days_ago(n))
        else:
            date_filter = ""
            params = (f'%{name}%',)

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT Employee_Name,
                       DATE_FORMAT(Date,'%%Y-%%m-%%d') as Date,
                       Status_Update, Issues, Completed_Task
                FROM Daily_Status_Update
                WHERE Employee_Name LIKE %s {date_filter}
                ORDER BY Date DESC
            """, params)
            rows = cursor.fetchall()
        return jsonify({"status": "success", "records": rows})
    except Exception as e:
        print("chatbot_status_by_name error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 9. DAILY STATUS — all employees ────────────────────────────
@app.route('/chatbot/all_status', methods=['POST'])
def chatbot_all_status():
    try:
        data = request.get_json()
        day  = data.get('day', 'today')

        if day == 'today':
            date_filter = "WHERE Date = %s"
            params = (_today(),)
        elif day == 'yesterday':
            date_filter = "WHERE Date = %s"
            params = (_yesterday(),)
        elif day == 'tomorrow':
            date_filter = "WHERE Date = %s"
            params = (_tomorrow(),)
        elif day.startswith('last_') and day.endswith('_days'):
            n = int(day.split('_')[1])
            date_filter = "WHERE Date >= %s"
            params = (_n_days_ago(n),)
        else:
            date_filter = ""
            params = ()

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT Employee_Name,
                       DATE_FORMAT(Date,'%%Y-%%m-%%d') as Date,
                       Status_Update, Issues, Completed_Task
                FROM Daily_Status_Update
                {date_filter}
                ORDER BY Date DESC, Employee_Name
            """, params)
            rows = cursor.fetchall()
        return jsonify({"status": "success", "records": rows})
    except Exception as e:
        print("chatbot_all_status error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── 10. ANNOUNCEMENTS ───────────────────────────────────────────
@app.route('/chatbot/announcements', methods=['POST'])
def chatbot_announcements():
    try:
        data = request.get_json()
        day  = data.get('day', 'all')

        if day == 'today':
            date_filter = "WHERE Announcement_date = %s"
            params = (_today(),)
        elif day == 'yesterday':
            date_filter = "WHERE Announcement_date = %s"
            params = (_yesterday(),)
        elif day == 'tomorrow':
            date_filter = "WHERE Announcement_date = %s"
            params = (_tomorrow(),)
        else:
            date_filter = ""
            params = ()

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT Employee_Name,
                       DATE_FORMAT(Announcement_date,'%%Y-%%m-%%d') as Announcement_date,
                       Announcement
                FROM Announcement
                {date_filter}
                ORDER BY Announcement_date DESC
            """, params)
            rows = cursor.fetchall()
        return jsonify({"status": "success", "records": rows})
    except Exception as e:
        print("chatbot_announcements error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
  # Run on port 5001 so Django views that target http://localhost:5001/* reach this Flask backend
  app.run(debug=True,host='0.0.0.0',port=5000)