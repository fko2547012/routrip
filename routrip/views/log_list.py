from django.views.generic import ListView
from models import Log


class LogListView(ListView):
    model = Log
    paginate_by = int

    def get_queryset(self):
        pass