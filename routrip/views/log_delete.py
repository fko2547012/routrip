from django.urls import reverse_lazy
from django.views.generic import DeleteView
from ..models import Log

class LogDeleteView(DeleteView):
    model = Log
    template_name = "routrip/log_delete.html"
    success_url = reverse_lazy("routrip:mypage")

    def get_queryset(self):
        return Log.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        pass