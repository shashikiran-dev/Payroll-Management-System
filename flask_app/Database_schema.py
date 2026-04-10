create_table_query_employee= """
    CREATE TABLE IF NOT EXISTS employee_complete_details (
    Employee_id VARCHAR(300) NOT NULL PRIMARY KEY,
    Employee_Name VARCHAR(200),
    Employee_email VARCHAR(255) UNIQUE NOT NULL, 
    Gender VARCHAR(200),
    Phone_Number VARCHAR(255),
    Date_of_birth VARCHAR(255),
    Address VARCHAR(255),
    Department VARCHAR(255),
    Position VARCHAR(255),
    Team_lead VARCHAR(255),
    Team_lead_email VARCHAR(255)  NOT NULL,
    Date DATE NOT NULL,
    Manager_name VARCHAR(255),
    Manager_email VARCHAR(255)  NOT NULL,
    Hire_date VARCHAR(255),
    Work_location VARCHAR(255),
    Skills VARCHAR(255),
    Emergency_contact VARCHAR(255),
    Username VARCHAR(255),
    Password VARCHAR(255),
    usertype VARCHAR(200)
);

    """  

create_table_query_UsersData= """
                CREATE TABLE IF NOT EXISTS users_Register_Data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email  VARCHAR(255)  UNIQUE,
                    usertype VARCHAR(255) NOT NULL
                )
            """

create_table_Query= """
    CREATE TABLE IF NOT EXISTS Doubts (
    query_id int primary key auto_increment,
    Employee_id VARCHAR(200),
    Employee_Name VARCHAR(300), 
    Employee_Email VARCHAR(200), 
    Date DATE,
    Time TIME,
    Query VARCHAR(300)
);
"""

create_table_query_birthday_wish= """
        CREATE TABLE IF NOT EXISTS Birthdays_Of_Employee
        (
          Employee_id VARCHAR(300),
          Employee_Name VARCHAR(255),
          Wished_On DATE,
          Wish VARCHAR(200),
          From_Employee_name VARCHAR(200)
        );

"""

create_table_query_employee_attendance= """
        CREATE TABLE IF NOT EXISTS Employee_Attendance_Data
        (
          Employee_id VARCHAR(300),
          FOREIGN KEY (Employee_id) REFERENCES employee_complete_details(Employee_id),
          employee_name VARCHAR(255) ,
          clock_in_time TIME ,
          clock_out_time TIME ,
          clock_in_location VARCHAR(255),
          clock_out_location VARCHAR(255),
          Avg_working_hrs TIME,
          Date DATE 
       );
         """

create_table_leave_request= """
    CREATE TABLE IF NOT EXISTS Leave_Request (
    Request_id VARCHAR(300)  NOT NULL PRIMARY KEY,
    Employee_id VARCHAR(300),
    FOREIGN KEY (Employee_id) REFERENCES employee_complete_details(Employee_id),
    Employee_Name VARCHAR(255),
    Applied_on DATE,
    Start_date DATE NOT NULL,
    End_date DATE NOT NULL,
    No_of_Days FLOAT,
    Leave_Type VARCHAR(400),
    Add_Employees VARCHAR(400),
    Reason VARCHAR(255),
    Status VARCHAR(255),
    Team_lead VARCHAR(255),
    Manager_name VARCHAR(255),
    Team_lead_email VARCHAR(255),
    Manager_email VARCHAR(255)  
);
    """  

create_table_leave_balance= """
    CREATE TABLE IF NOT EXISTS Leave_balance (
    Employee_id VARCHAR(300),
    FOREIGN KEY (Employee_id) REFERENCES employee_complete_details(Employee_id),
    Employee_Name VARCHAR(200),
    Employee_email VARCHAR(300),
    Gender VARCHAR(200),
    Sick_Leave FLOAT,
    Wedding_Leave FLOAT,
    Maternity_Leave FLOAT,
    Paternity_Leave FLOAT,
    No_of_leaves FLOAT,
    Taken_leaves FLOAT,
    Pending_leaves FLOAT
);
    """  
create_table_daily_status= """
    CREATE TABLE IF NOT EXISTS Daily_Status_Update (
    Employee_id VARCHAR(300),
    FOREIGN KEY (Employee_id) REFERENCES employee_complete_details(Employee_id),
    Employee_Name VARCHAR(200),
    Employee_Email VARCHAR(200),
    Date DATE,
    Time TIME,
    Status_Update VARCHAR(300),
    Issues VARCHAR(300),
    Completed_Task VARCHAR(200),
    Feature_Targets VARCHAR(300)
);
    """  
create_table_leave_history= """
    CREATE TABLE IF NOT EXISTS Leave_history (
    Request_id VARCHAR(300), 
    Employee_id VARCHAR(300),
    FOREIGN KEY (Employee_id) REFERENCES employee_complete_details(Employee_id),
    Employee_Name VARCHAR(255),
    Start_date DATE ,
    End_date DATE ,
    No_of_Days INT,
    Leave_Type VARCHAR(400),
    Approved_By_Whom VARCHAR(300),
    Add_Employees VARCHAR(400),
    Reason VARCHAR(255),
    Status VARCHAR(255),
    Team_lead VARCHAR(255),
    Manager_name VARCHAR(255),
    Team_lead_email VARCHAR(255),
    Manager_email VARCHAR(255)  
);
    """  
create_table_holiday= """
    CREATE TABLE IF NOT EXISTS Holiday (
    Festival_name VARCHAR(200),
    Holiday_date DATE
);
    """  
create_table_Announcement= """
    CREATE TABLE IF NOT EXISTS Announcement (
    Employee_id VARCHAR(300),
    FOREIGN KEY (Employee_id) REFERENCES employee_complete_details(Employee_id),
    Employee_Name VARCHAR(200),
    Announcement VARCHAR(200),
    Inserting_date DATE,
    Announcement_date DATE   
);
    """  



create_table_work_from_Home= """
    CREATE TABLE IF NOT EXISTS Work_From_Home (
    Request_id VARCHAR(300)  NOT NULL PRIMARY KEY,
    Employee_id VARCHAR(300),
    FOREIGN KEY (Employee_id) REFERENCES employee_complete_details(Employee_id),
    Employee_Name VARCHAR(255),
    Applied_on DATE,
    Start_Date DATE NOT NULL,
    End_Date DATE NOT NULL,
    No_of_Days FLOAT,
    Reason VARCHAR(255),
    Status VARCHAR(255),
    Team_lead VARCHAR(255),
    Manager_name VARCHAR(255),
    Team_lead_email VARCHAR(255),
    Manager_email VARCHAR(255),
    Approved_By_Whom Varchar(200) 
);
"""

create_table_Clock_Adj= """
    CREATE TABLE IF NOT EXISTS ClockAdjustment (
    Employee_id VARCHAR(300),
    FOREIGN KEY (Employee_id) REFERENCES employee_complete_details(Employee_id),
    Employee_Name VARCHAR(200),
    Request_Type VARCHAR(200),
    Clock_In TIME ,
    Clock_Out TIME ,
    Reason VARCHAR(200),
    Selected_Date Date,
    Time_of_Day Varchar(200),
    Inserting_Date DATE,
    Request_Status Varchar(200)    
);
    """  