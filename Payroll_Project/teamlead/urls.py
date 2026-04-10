from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.teamlead_dashboard, name='teamlead_dashboard'),

    # My Team
    path('my-team/', views.my_team_members, name='teamlead_my_team'),
    path('my-team/profile/<str:emp_id>/', views.team_member_profile, name='team_member_profile'),

    # Leave
    path('leave-requests/', views.team_leave_requests, name='teamleave_requests'),
    path('leave-accept/<str:leave_id>/<str:name>/', views.team_leave_accept, name='teamleave_accept'),
    path('leave-reject/<str:leave_id>/<str:name>/', views.team_leave_reject, name='teamleave_reject'),
    path('leave-history/', views.team_leave_history, name='team_leave_history'),

    # WFH
    path('wfh-requests/', views.team_wfh_requests, name='team_wfh_requests'),
    path('wfh-update/<str:req_id>/<str:action>/', views.team_wfh_update, name='team_wfh_update'),
    path('wfh-history/', views.team_wfh_history, name='team_wfh_history'),

    # Attendance
    path('attendance/', views.team_attendance_overview, name='team_attendance'),
    path('attendance/history/', views.team_attendance_history, name='team_attendance_history'),

    # Daily Status
    path('daily-status/', views.team_daily_status, name='team_daily_status'),
    path('daily-status/history/', views.team_status_history, name='team_status_history'),

    # Clock Adjustments
    # Flask accept: /accept_req/<Employee_Id>/<Request_Type>/<Selected_Date>/<person_name>/<Employee_Name>
    # Flask reject: /reject_req/<Employee_Id>/<Selected_Date>/<Request_Type>/<person_name>
    path('clock-adjustments/', views.team_clock_adjustments, name='team_clock_adjustments'),
    path('clock-adjust-action/<str:emp_id>/<str:req_type>/<str:selected_date>/<str:person_name>/<str:emp_name>/',
         views.team_clock_adjust_action, name='team_clock_adjust_action'),
    path('clock-adjustments/history/', views.team_clock_adj_history, name='team_clock_adj_history'),

    # Queries
    path('queries/', views.team_queries, name='team_queries'),
    path('reply-query/<str:query_id>/', views.reply_query, name='teamlead_reply_query'),
    path('my-queries/', views.teamlead_my_queries, name='teamlead_my_queries'),

    # Announcements
    path('announcements/', views.team_announcements, name='team_announcements'),

    # Team Dashboard (tabbed)
    path('team-dashboard/', views.team_dashboard, name='team_dashboard'),

    # Own Attendance
    path('my-attendance/', views.teamlead_own_attendance, name='teamlead_own_attendance'),

    path('teamlead/analytics/', views.teamlead_analytics, name='teamlead_analytics')
]
