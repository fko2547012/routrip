from urllib import request
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Log


class MypageView(LoginRequiredMixin, TemplateView):
    template_name = 'routrip/mypage.html'
    login_url = 'routrip:login'
    def get_context_data(self, **kwargs):
        # マイログ取得
        context = super().get_context_data(**kwargs)
        context['mylog'] = Log.objects.filter(user = self.request.user).order_by("-posted_at")
        context["editing"] = self.request.GET.get("edit")
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "name":
        # ユーザー名保存
            request.user.display_name = request.POST("display_name")
        elif action == "privacy":
        # 公開設定
            request.user.is_public = (request.POST.get("is_public") == "True")
        
        request.user.save()
        return redirect("routrip:mypage")