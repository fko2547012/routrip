from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Log


class MypageView(LoginRequiredMixin, TemplateView):
    template_name = 'routrip/mypage.html'
    login_url = 'routrip:login'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mylog'] = Log.objects.filter(user = self.request.user).order_by("-posted_at")
        return context