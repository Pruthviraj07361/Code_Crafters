from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


def _frontend_destination(user):
	if not user.is_authenticated:
		return 'frontend-preview'

	if user.is_superuser:
		return 'frontend-preview-supervisor'

	profile = getattr(user, 'admin_profile', None)
	if profile is not None:
		return {
			'faculty': 'frontend-preview-faculty',
			'supervisor': 'frontend-preview-supervisor',
			'superuser': 'frontend-preview-supervisor',
		}.get(profile.staff_type, 'frontend-preview')

	return 'frontend-preview-student'


def register(request):
	return redirect('frontend-preview')


def login_view(request):
	return redirect(_frontend_destination(request.user))


def profile(request):
	return redirect(_frontend_destination(request.user))


def logout_view(request):
	if request.method == 'POST':
		logout(request)
		messages.info(request, 'You have been logged out.')
	return redirect('frontend-preview')
