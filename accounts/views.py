from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import views as auth_views, login
from .forms import LoginForm, RegisterForm


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_analyst:
            return '/analytics/'
        return '/dashboard/'


class LogoutView(auth_views.LogoutView):
    next_page = '/accounts/login/'
    # Django 5.x: LogoutView already accepts POST by default.
    # We also allow GET so the sidebar link works.
    http_method_names = ['get', 'post', 'options']

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}! Your account has been created.')
            return redirect('/dashboard/')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})
