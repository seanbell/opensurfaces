from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

import account.views

from accounts.models import UserProfile
from accounts.forms import SignupForm, LoginUsernameOrEmailForm


@staff_member_required
def admin_shell(request):
    return render(request, "admin_shell.html", {
        'ADMIN_SHELL_PASSWORD': settings.ADMIN_SHELL_PASSWORD,
        'ADMIN_SHELL_PORT': settings.ADMIN_SHELL_PORT,
        'SERVER_IP': settings.SERVER_IP
    })


class SignupView(account.views.SignupView):
    form_class = SignupForm


class SignupViewAjax(account.views.SignupView):
    form_class = SignupForm
    template_name = 'account/signup_ajax.html'


class LoginView(account.views.LoginView):
    form_class = LoginUsernameOrEmailForm


class LoginViewAjax(account.views.LoginView):
    form_class = LoginUsernameOrEmailForm
    template_name = 'account/login_ajax.html'


## Old, unused stuff:

class UserProfileListView(ListView):
    model = UserProfile

    def get_context_data(self, **kwargs):
        context = super(UserProfileListView, self).get_context_data(**kwargs)
        #context['now'] = timezone.now()
        return context


class UserProfileDetailView(DetailView):
    model = UserProfile

    def get_context_data(self, **kwargs):
        context = super(UserProfileDetailView, self).get_context_data(**kwargs)
        #context['now'] = timezone.now()
        return context
