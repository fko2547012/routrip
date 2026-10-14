from collections import defaultdict, deque

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..models import Log, Logcard, Tag, Section, Spot
from ..forms.log import LogForm, LogCardFormSet



class LogUpdateView(LoginRequiredMixin, UpdateView):
    model = Log
    form_class = LogForm
    template_name = 'routrip/log_edit.html'
    context_object_name = 'log'
    login_url = 'routrip:login'

    def get_queryset(self):
        #本人が登録済したタグだけを編集対象にする
        queryset = super().get_queryset().filter(
            user=self.request.user
            )
        if self.request.user.method == 'POST':
            queryset = queryset.select_for_update()
            
        return queryset
        
    def get_initial(self):
        #登録済みのタグを入力欄に表示する
        initial = super().get_initial()
        
        initial['tags_text'] = ', '.join(
            self.object.tags.order_by('name').values_list('name', flat=True)
        )
        return initial
    
    def get_form(self, form_class=None):
        #保存済みの日付を入力欄に表示する
        form = super().get_form(form_class)
        
        for name in ('trip_start_date', 'trip_end_date'):
            form.fields[name].widget = forms.DateInput(format='%Y-%m-%d',
            attrs={'type': 'date'})
        return form
    
    def get_formset(self):
        #登録済みカードと、手前の移動区間を読み込み
        
        kwargs = {
            'instance': self.object,
            'prefix': 'cards',
            'queryset': Logcard.objects.cards.order_by(
                'display_order','id'
            ),
        }
        
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
            
    formset = EditCardFormSet(**kwargs)
    
    #同じスポット間を何度も移動する場合も対応   
    sections=defaultdict(deque)
    for section in self.object.sections.order_by(
        'section_order','id'
        ):
        key=(section.form_spot_id,section.to_spot_id)
        sections[key].append(section)
        
        prev_spot_id=self.object.start_spot_id

        
            
    
    
    def get_success_url(self):
        #ログ詳細画面にリダイレクトする
        return reverse('routrip:log_detail', kwargs={'pk': self.object.pk})