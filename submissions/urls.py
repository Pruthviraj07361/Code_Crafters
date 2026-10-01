from django.urls import path

from . import views

urlpatterns = [
    path('student/problem-statements/<int:pk>/submit', views.student_submit_problem),
    path('student/submissions', views.student_submissions),
    path('student/submissions/<int:pk>', views.student_submission_detail),
]
