from django.views.generic import DetailView
from ..models import Log


class LogDetailView(DetailView):
    model = Log

    def get_context_data():
        pass
