Great — now I can see your **actual code**, so here is a **100% accurate README based on your project implementation** (not generic). I’ve aligned everything with your `views.py`, `urls.py`, and `models.py`.

---

# 💼 Payroll Management System

A **full-stack Payroll & Employee Management System** built using **Django (Frontend & Controller)** and **Flask (Backend APIs)**.
The system handles **attendance tracking, payroll-related operations, leave management, work-from-home tracking, and analytics dashboards** for different user roles.

---

## 📌 Project Overview

This application is designed to manage organizational workflows including:

* Employee attendance (Clock-in / Clock-out with location)
* Leave requests and approvals
* Work From Home (WFH) management
* Admin analytics dashboard
* Employee status tracking
* Chatbot integration for assistance

The system follows a **microservice-like architecture**:

* **Django** → UI + session management
* **Flask API** → Business logic & database operations

---

## 🏗️ Architecture

```
Django (Frontend + Views)
        ↓
   REST API Calls
        ↓
Flask Backend (Port: 5000)
        ↓
     Database
```

---

## 🚀 Features (Based on Your Code)

### 🔐 Authentication & Session Management

* Login via Flask API (`/login`) 
* Session-based authentication (`login_required`)
* Role-based redirection:

  * Employer → Admin Dashboard
  * Team Lead → Team Dashboard
  * Employee → Clock Page

---

### ⏱️ Attendance System

* Clock-in / Clock-out with **live location tracking**
* Uses reverse geocoding API for location
* Attendance history with calendar view
* Fetches data from Flask:

  * `/get_clock_in`
  * `/get_attendance_data` 

---

### 📊 Admin Analytics Dashboard

* Total employees count
* Leave statistics (Pending / Approved / Rejected)
* Work From Home insights
* Daily attendance trends
* Monthly top & bottom performers

📍 Implemented in: `admin_analytics()` 

---

### 🏠 Work From Home (WFH)

* Apply for WFH
* Admin approval/rejection
* Tracks:

  * Start date / End date
  * Status (Pending, Accepted, Rejected)

---

### 📝 Leave Management

* Apply leave
* View:

  * Pending
  * Accepted
  * Rejected
* Admin can:

  * Approve / Reject leave requests

Endpoints used:

* `/leave_request_data`
* `/accepted_leave_history`
* `/get_leaverequest_data` 

---

### 📅 Employee Status Tracking

* Daily work updates
* Fetch status by date or range
* Export reports to Excel

---

### 📥 Export Features

* Download attendance/status reports as Excel
* Implemented using `openpyxl`
* Function: `generate_excel()` 

---

### 🤖 Chatbot Integration

* Chatbot API endpoint available:

  * `/chatbot-api/` 
* Used for payroll-related queries

---

### 🏢 Organization Structure

* Displays hierarchy:

  * Manager → Team Lead → Employees
* Built using nested dictionary logic

---

### 🔔 Notifications & Announcements

* Admin announcements
* Employee notifications
* Query reply system

---

## 🛠️ Tech Stack

| Layer        | Technology                   |
| ------------ | ---------------------------- |
| Frontend     | HTML, CSS, JavaScript        |
| Backend      | Django                       |
| API Layer    | Flask                        |
| Database     | (Handled by Flask backend)   |
| Excel Export | openpyxl                     |
| APIs         | REST APIs (requests library) |

---

## 📂 Project Structure

```
Payroll-Management-System/
│
├── app/
│   ├── views.py          # Core business logic (Django controller)
│   ├── models.py        # Registration model
│   ├── urls.py          # URL routing
│
├── templates/           # HTML templates
├── static/              # CSS & JS
├── manage.py
└── requirements.txt
```

---

## 🧩 Database Model

### Registration Model

```python
class Registration(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    Email = models.EmailField()
    UserType = models.CharField(choices=...)
```



---

## 🔗 Important Routes

### Authentication

* `/login/`
* `/logout/`
* `/forgot_password/`

### Employee

* `/clock/`
* `/attendance_data/`
* `/leave/`

### Admin

* `/admin/analytics/`
* `/search/`
* `/get_Employee_Leaves/`
* `/org/`

### Chatbot

* `/chatbot-api/`



---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/shashikiran-dev/Payroll-Management-System.git
cd Payroll-Management-System
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run Django Server

```bash
python manage.py runserver
```

### 5️⃣ Run Flask Backend

```bash
cd backend   # (your Flask folder)
python app.py
```

---

## ▶️ Usage Flow

1. Login using credentials
2. Based on role:

   * Admin → Analytics Dashboard
   * Employee → Clock-in system
   * Team Lead → Team dashboard
3. Perform actions:

   * Mark attendance
   * Apply leave
   * Track performance
   * View reports

---

## 📊 Key Highlights

* 🔄 Django ↔ Flask API integration
* 📍 Location-based attendance
* 📈 Advanced analytics dashboard
* 📤 Excel export functionality
* 🔐 Secure session management

---

## 🔮 Future Enhancements

* 📱 Mobile app version
* ☁️ Cloud deployment (AWS)
* 📧 Email notifications for payroll
* 🤖 Advanced AI chatbot
* 📊 Salary calculation module

---

## 👨‍💻 Author

**Shashi Kiran**
📧 [shashikuruva2004@gmail.com](mailto:shashikuruva2004@gmail.com)
🎓 G. Pulla Reddy Engineering College

---

## ⭐ Support

If you like this project:

* ⭐ Star the repository
* 🍴 Fork it
* 🤝 Contribute

