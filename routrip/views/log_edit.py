from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from models import Log
from forms import LogForm


class LogUpdateView(LoginRequiredMixin, UpdateView):
    model = Log
    form_class = LogForm

    def form_valid(self, form):
        pass