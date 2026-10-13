from django.views import View
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from ..models import Log, Tag, Section
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

        prev_spot = self.object.start_spot  # 最初の出発側は、出発スポット
        order = 0
        for card_form in formset.forms:
            if not card_form.has_changed(): # 何も入力されていない欄は無視
                continue
            order += 1
            card = card_form.save(commit=False)
            card.log = self.object
            card.display_order = order
            card.save() # カードを保存

            Section.objects.create( # 手前の移動区間を保存
                log=self.object,
                from_spot=prev_spot,
                to_spot=card.spot,
                section_order=order,
                transport=card_form.cleaned_data['transport'],
                duration=card_form.cleaned_data['duration'],
            )
            prev_spot = card.spot   # 次のカードの出発側にする
        return response

    # def success_url(self):
    #     pass

class LogImageSelectView(LoginRequiredMixin, View):
    """
    ログ作成時の画像選択ビュー
    """
    template_name = 'routrip/log_create_images.html'

    def get(self, request):
        """
        画像選択画面を表示する
        """
        return render(request, self.template_name)