from django.urls import reverse_lazy
from django.views.generic import CreateView
from ..forms.account import SignUpForm
from django.contrib.auth.views import LoginView,LogoutView
from ..forms.account import LoginForm

class SignUpView(CreateView):
    form_class=SignUpForm
    template_name="routrip/signup.html"
    success_url=reverse_lazy("routrip:login")

class CustomLoginView(LoginView):
    template_name="routrip/login.html"
    form_class=LoginForm

    def get_success_url(self):
        return reverse_lazy("routrip:top_page")

class CustomLogoutView(LogoutView):
    next_page=reverse_lazy("routrip:top_page")    