from django.urls import path

from .consumers import SubmissionConsumer


websocket_urlpatterns = [
    path('ws/submissions/<int:submission_id>/', SubmissionConsumer.as_asgi()),
]