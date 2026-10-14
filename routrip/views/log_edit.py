from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.db import transaction
from django.urls import reverse
from ..models import Log,Tag
from ..forms.log import LogForm


class LogUpdateView(LoginRequiredMixin, UpdateView):
    model = Log
    form_class = LogForm
    template_name = 'routrip/log_edit.html'
    context_object_name = 'log'
    login_url = 'routrip:login'

    def get_queryset(self):
        #本人が登録済したタグだけを編集対象にする
        return super().get_queryset().filter(
            user=self.request.user
            )
        
    def get_initial(self):
        #登録済みのタグを入力欄に表示する
        initial = super().get_initial()
        
        initial['tags_text'] = ', '.join(
            self.object.tags.order_by('name').values_list('name', flat=True)
        )
        return initial
    
    def form_form(self, form_class=None):
        #保存済みの日付を入力欄に表示する
        form = super().get_form(form_class)
        
        for field in ('trip_start_date', 'trip_end_date'):
            form.fields[field].widget.format = '%Y-%m-%d'
        return form
    
    def form_valid(self, form):
        #入力内容とタグをまとめて保存する
        with transaction.atomic():
            #ログを更新
            response = super().form_valid(form)
            
            #入力されたタグを取得、ない場合は作成
            tags=[]
            
            for name in form.cleaned_data['tags_text']:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
                
                #以前のタグを新しく置き換え
            self.object.tags.set(tags)
            
            return response
        
    def get_success_url(self):
        #ログ詳細画面にリダイレクトする
        return reverse('routrip:log_detail', kwargs={'pk': self.object.pk})