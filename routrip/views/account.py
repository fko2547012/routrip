from django.urls import reverse_lazy
from django.views.generic import CreateView
from ..forms.account import SignUpForm

class SignUpView(CreateView):
    form_class=SignUpForm
    template_name="signup.html"
    success_url=reverse_lazy("login")
    