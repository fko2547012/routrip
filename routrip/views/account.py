from django.urls import reverse_lazy
from django.views.generic import CreateView
from ..forms.account import SignUpForm
from django.contrib.auth.views import LoginView,LogoutView
from ..forms.account import LoginForm
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.views import View

class SignUpView(CreateView):
    form_class=SignUpForm
    template_name="routrip/signup.html"
    success_url=reverse_lazy("routrip:login")

class CustomLoginView(LoginView):
    template_name="routrip/login.html"
    form_class=LoginForm

    def get_success_url(self):
        return reverse_lazy("routrip:top_page")

# class CustomLogoutView(LogoutView):
#     template_name="routrip/logout.html"
class CustomLogoutView(View):
    def get(self, request):
        return render(request, "routrip/logout.html")

    def post(self, request):
        logout(request)
        return redirect("routrip:top_page")