from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def register(request):
	if request.user.is_authenticated:
		return redirect('accounts:profile')

	form = UserCreationForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		login(request, user, backend='django.contrib.auth.backends.ModelBackend')
		messages.success(request, 'Your account has been created.')
		return redirect('accounts:profile')

	return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
	if request.user.is_authenticated:
		return redirect('accounts:profile')

	form = AuthenticationForm(request, data=request.POST or None)
	if request.method == 'POST' and form.is_valid():
		login(request, form.get_user())
		next_url = request.POST.get('next') or request.GET.get('next')
		if next_url and url_has_allowed_host_and_scheme(
			next_url,
			allowed_hosts={request.get_host()},
			require_https=request.is_secure(),
		):
			return redirect(next_url)
		return redirect('accounts:profile')

	return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile(request):
	return render(request, 'accounts/profile.html')


def logout_view(request):
	if request.method == 'POST':
		logout(request)
		messages.info(request, 'You have been logged out.')
	return redirect('accounts:login')
