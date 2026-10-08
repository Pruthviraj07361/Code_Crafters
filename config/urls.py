"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='frontend-preview', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path('preview/', TemplateView.as_view(template_name='frontend/loginpg.html'), name='frontend-preview'),
    path('preview/login/', TemplateView.as_view(template_name='frontend/loginpg.html'), name='frontend-preview-login'),
    path('preview/student/', TemplateView.as_view(template_name='frontend/studentddashboardpg.html'), name='frontend-preview-student'),
    path('preview/faculty/', TemplateView.as_view(template_name='frontend/facultypg.html'), name='frontend-preview-faculty'),
    path('preview/submission/', TemplateView.as_view(template_name='frontend/pssubmissionpg.html'), name='frontend-preview-submission'),
    path('preview/supervisor/', TemplateView.as_view(template_name='frontend/supervisorpg.html'), name='frontend-preview-supervisor'),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('api/', include('accounts.api_urls')),
    path('api/', include('assignments.urls')),
    path('api/', include('submissions.urls')),
]
