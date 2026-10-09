from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from ..models import Log, Tag
from ..forms.log import LogForm, LogCardFormSet


class LogCreateView(LoginRequiredMixin, CreateView):
    """
    ログ作成ビュー
    """
    model = Log
    form_class = LogForm
    template_name = 'routrip/log_create.html'
    success_url = reverse_lazy('routrip:top_page') #後で変更

    def get_context_data(self, **kwargs):
        """
        カードのフォームセットを画面に表示するコンテキスト
        """
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = LogCardFormSet(
                self.request.POST, self.request.FILES)
        else:
            context['formset'] = LogCardFormSet()
        return context

    def form_valid(self, form):
        """
        formの入力値をチェックして、ログとタグを保存する
        """
        formset = LogCardFormSet(self.request.POST, self.request.FILES)
        if not formset.is_valid():
            return self.form_invalid(form)  #ログの入力画面を再表示する

        form.instance.user = self.request.user 
        response = super().form_valid(form) #ログを保存

        for name in form.cleaned_data['tag_text']:
            tag, _ = Tag.objects.get_or_create(name=name)   #タグを取得または作成
            self.object.tags.add(tag)   #ログにタグを追加

        formset.instance = self.object
        cards = formset.save(commit=False)  #カードを保存するが、まだDBには保存しない
        for order, card in enumerate(cards, start=1):
            card.display_order = order
            card.save() #カードをDBに保存
        return response

    # def success_url(self):
    #     pass