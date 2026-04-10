from django.contrib import admin
from django.urls import path, include
from . import views
from django.urls import path
from .views import chatbot_api

urlpatterns = [

    # ── Auth ──────────────────────────────────────────────────────────────
    path('',                        views.home,             name='home'),
    path('login/',                  views.user_login,       name='login'),
    path('logout/',                 views.logout,           name='logout'),
    path('forgot_password/',        views.forgot_password,  name='forgot_password'),
    path('validate_password/<str:keyword>/', views.validate_password, name='validate_password'),

    # ── Employee — Clock / Attendance ─────────────────────────────────────
    path('clock/',                  views.clock,            name='clock'),
    path('attendance_data/',        views.attendance_data,  name='attendance_data'),
    path('get_specific_data/',      views.get_specific_data,name='get_specific_data'),
    path('update_location/',        views.update_location,  name='update_location'),

    # ── Employee — Leave ──────────────────────────────────────────────────
    path('leave/',                  views.leave,            name='leave'),
    path('LeaveManagement/',        views.leaveManagement,  name='LeaveManagement'),
    path('check/',                  views.check,            name='check'),
    path('accept/',                 views.accept,           name='accept'),
    path('reject/',                 views.reject,           name='reject'),
    path('pending/',                views.pending,          name='pending'),
    path('Partial_Leave/',          views.Partial_Leave,    name='Partial_Leave'),

    # ── Employee — WFH ────────────────────────────────────────────────────
    path('work_from_home/',         views.work_from_home,   name='work_from_home'),

    # ── Employee — Status / Profile ───────────────────────────────────────
    path('statusCheck/',            views.statusCheck,      name='statusCheck'),
    path('get_Status_Data/',        views.get_Status_Data,  name='get_Status_Data'),
    path('update_Status/',          views.update_Status,    name='update_Status'),
    path('status/',                 views.status,           name='status'),
    path('status_update/',          views.status_update,    name='status_update'),
    path('profile/',                views.profile,          name='profile'),

    # ── Employee — Queries / Notifications ───────────────────────────────
    path('queries/',                views.Queries_Data,     name='Queries_Data'),
    path('Birthday_Data/',          views.Birthday_Data,    name='Birthday_Data'),
    path('notification_Data/<str:username>/<str:email>/<str:user_id>/<str:user_type>',
         views.notification_Data, name='notification_Data'),

    # ── Admin — Dashboard / Search ────────────────────────────────────────
    path('search/',                 views.search,           name='search'),
    path('admin/analytics/',        views.admin_analytics,  name='admin_analytics'),
    path('opening/<str:username>/<str:user_type>/<str:email>/<str:user_id>',
         views.opening, name='opening'),

    # ── Admin — Leave ─────────────────────────────────────────────────────
    path('get_Employee_Leaves/',    views.get_Employee_Leaves,  name='get_Employee_Leaves'),
    path('leave_status/',           views.leave_status,         name='leave_status'),
    # Use str (not int) — request_id is a 4-digit string like "0819"
    path('leave_accept/<str:request_id>/', views.leave_accept,  name='leave_accept'),
    path('leave_reject/<str:request_id>/', views.leave_reject,  name='leave_reject'),

    # ── Admin — Attendance ────────────────────────────────────────────────
    path('get_Employee_Attendance/', views.get_Employee_Attendance, name='get_Employee_Attendance'),
    path('Attendance_Info/<str:username>/<str:user_type>/<str:email>/<str:user_id>/<str:Request_type>/<str:Emp_id>',
         views.Attendance_Info, name='Attendance_Info'),

    # ── Admin — WFH ───────────────────────────────────────────────────────
    path('get_Employee_WFHInfo/',   views.get_Employee_WFHInfo,     name='get_Employee_WFHInfo'),
    path('wfh_accept/<str:request_id>/', views.wfh_accept,          name='wfh_accept'),
    path('wfh_reject/<str:request_id>/', views.wfh_reject,          name='wfh_reject'),
    # Legacy — keep for old email links; routes internally to wfh_accept/reject
    path('Work_From_Home_Action/<str:Request_id>/<str:username>/<str:user_type>/<str:email>/<str:user_id>/<str:action>/',
         views.Work_From_Home_Action, name='Work_From_Home_Action'),
    path('Work_From_Home_accept/<str:Request_id>/', views.Work_From_Home_accept, name='Work_From_Home_accept'),
    path('Work_From_Home_Reject/<str:Request_id>/<str:user_name>/<str:user_type>/<str:email>/<str:user_id>',
         views.Work_From_Home_Reject, name='Work_From_Home_Reject'),
    path('Work_from_home_accept/', views.Work_from_home_accept, name='Work_from_home_accept'),
    path('update_action_status/',  views.update_action_status,  name='update_action_status'),

    # ── Admin — Daily Status ──────────────────────────────────────────────
    path('AdminStatusInfo/',        views.AdminStatusInfo,  name='AdminStatusInfo'),
    path('Status_Info/',            views.Status_Info,      name='Status_Info'),
    path('get_Employee_status/<str:username>/<str:user_type>/<str:email>/<str:user_id>',
         views.get_Employee_status, name='get_Employee_status'),

    # ── Admin — Organisation / Employee Management ────────────────────────
    path('org/',                    views.org,              name='org'),
    path('update/<str:Employee_id>/', views.update,         name='update'),
    path('submit_employee_data/<str:Request_type>/', views.submit_employee_data, name='submit_employee_data'),
    path('Admin_MyTeam_Info/',      views.Admin_MyTeam_Info,name='Admin_MyTeam_Info'),

    # ── Admin — Announcements ─────────────────────────────────────────────
    path('Announcements_Data/',     views.Announcements_Data,   name='Announcements_Data'),
    path('Announcements_admin/<str:username>/<str:user_type>/<str:email>/<str:user_id>',
         views.Announcements_admin, name='Announcements_admin'),
    path('Announcement/<str:Date>/<str:username>/<str:user_type>/<str:email>/<str:user_id>',
         views.Announcement, name='Announcement'),
    path('Announcement_Update/<str:Date>/', views.Announcement_Update, name='Announcement_Update'),
    path('update_announce/<str:Selected_Date>/', views.update_announce, name='update_announce'),
    path('delete_announcement_view/<str:Announcement_date>/<str:Announcement>/',
         views.delete_announcement_view, name='delete_announcement_view'),

    # ── Admin — Holidays / Festivals ─────────────────────────────────────
    path('festival_data/',          views.festival_data,    name='festival_data'),
    path('Fest_Info/',              views.Fest_Info,        name='Fest_Info'),
    path('Admin_Holiday_Info/<str:username>/<str:user_type>/<str:email>/<str:user_id>',
         views.Admin_Holiday_Info,  name='Admin_Holiday_Info'),

    # ── Admin — Notifications ─────────────────────────────────────────────
    path('Admin_notification_Data/<str:username>/<str:email>/<str:user_id>/<str:user_type>',
         views.Admin_notification_Data, name='Admin_notification_Data'),
    path('reply_query/<int:query_id>/', views.reply_query,  name='reply_query'),
    path('admin_chatbot/', views.admin_chatbot, name='admin_chatbot'),

    # ── Clock Adjustment ──────────────────────────────────────────────────
    path('ClockAdj_Data/<str:Date>/<str:username>/<str:user_type>/<str:email>/<str:user_id>',
         views.ClockAdj_Data, name='ClockAdj_Data'),
    path('Clock_Adjustment/<str:request_type>/<str:username>/<str:user_type>/<str:email>/<str:user_id>',
         views.Clock_Adjustment, name='Clock_Adjustment'),

    # ── Downloads ─────────────────────────────────────────────────────────
    path('Pdf_Download/<str:username>/<str:user_type>/<str:email>/<str:user_id>/<str:start_date>/<str:end_date>',
         views.Pdf_Download, name='Pdf_Download'),
    path('generate_excel/<str:username>/<str:user_type>/<str:email>/<str:user_id>/<str:start_date>/<str:end_date>/',
         views.generate_excel, name='generate_excel'),

     #-----Team Lead Urls-----
     path('teamlead/', include('teamlead.urls')),

     


     path('chatbot-api/', views.chatbot_api, name='chatbot_api'),
     path('chatbot/', views.admin_chatbot, name='admin_chatbot'),

]
