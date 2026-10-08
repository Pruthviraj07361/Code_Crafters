from django.urls import path

from . import api_views

urlpatterns = [
    path('auth/student/register', api_views.register_student),
    path('auth/admin/register', api_views.register_admin),
    path('auth/login', api_views.login),
    path('auth/me', api_views.current_user),
    path('auth/me/profile', api_views.update_student_profile),
    path('faculty/pending-students', api_views.pending_students),
    path('faculty/students/<int:pk>/approve', api_views.approve_student),
    path('faculty/activity', api_views.activity_log),
    path('superuser/pending-staff', api_views.pending_staff),
    path('superuser/staff/<int:pk>/assign-role', api_views.assign_staff_role),
]
