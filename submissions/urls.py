from django.urls import path

from . import views

urlpatterns = [
    path('supervisor/student-progress', views.supervisor_student_progress),
    path(
        'supervisor/students/<int:student_id>/submissions',
        views.supervisor_student_submissions,
    ),
    path(
        'supervisor/students/<int:student_id>/submissions/<int:pk>',
        views.supervisor_student_submission_detail,
    ),
    path('student/problem-statements/<int:pk>/submit', views.student_submit_problem),
    path('student/problem-statements/<int:pk>/submit-live', views.student_submit_problem_live),
    path('student/submissions', views.student_submissions),
    path('student/submissions/<int:pk>', views.student_submission_detail),
]
