from django.contrib import admin

from .models import AdminProfile, StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'enrollment_number', 'division', 'branch', 'is_approved')
    list_filter = ('is_approved', 'division', 'branch')
    search_fields = ('name', 'enrollment_number', 'user__email')


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'staff_type', 'is_approved')
    list_filter = ('staff_type', 'is_approved')
    search_fields = ('name', 'user__email')
