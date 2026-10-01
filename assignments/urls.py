from django.urls import path

from . import views

urlpatterns = [
    path('supervisor/problem-statements', views.supervisor_problem_statements),
    path('supervisor/meeting', views.supervisor_meeting),
    path('student/problem-statements', views.student_problem_statements),
    path('student/problem-statements/<int:pk>', views.student_problem_statement_detail),
    path('student/meeting', views.student_meeting),
]
