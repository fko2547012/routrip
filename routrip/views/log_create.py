from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Log
from ..forms.log import LogForm, LogCardFormSet


class LogCreateView(CreateView):
    model = Log
    form_class = LogForm
    template_name = 'logs/log_create.html'

    def get_context_data(self, **kwargs):
        pass

    def form_valid(self, form):
        pass

    def success_url(self):
        pass