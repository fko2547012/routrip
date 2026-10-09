from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from ..models import Log, Tag
from ..forms.log import LogForm


class LogCreateView(CreateView):
    model = Log
    form_class = LogForm
    template_name = 'routrip/log_create.html'
    success_url = reverse_lazy('routrip:top_page') #後で変更

    # def get_context_data(self, **kwargs):
    #     pass

    def form_valid(self, form):
        """
        formの入力値をチェックして、ログとタグを保存する
        """
        form.instance.user = self.request.user 
        response = super().form_valid(form) #ログを保存
        for name in form.cleaned_data['tag_text']:
            tag, _ = Tag.objects.get_or_create(name=name)   #タグを取得または作成
            self.object.tags.add(tag)   #ログにタグを追加
        return response

    # def success_url(self):
    #     pass