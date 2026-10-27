from itertools import zip_longest
from django.contrib import messages
from django.shortcuts import redirect
from django.http import Http404
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from ..models import Log


class LogDetailView(LoginRequiredMixin, DetailView):
    model = Log
    template_name = 'routrip/log_detail.html'
    context_object_name = 'log'
    
    def get_queryset(self):
        #ログを取得する
        return (
            super().get_queryset()
            .filter(Q(user__is_public=True)
                    | Q(user=self.request.user)
                    )
        .select_related('user', 'start_spot')
        )
        
    def get(self, request, *args, **kwargs):
        #ログが既に削除されて見つからない時
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            messages.error(request, 'このログが見つかりませんでした。')
            return redirect('routrip:log_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log = self.object
        
        #カードを表示順に取得
        cards = list(
            log.cards
            .select_related('spot')
            .order_by('display_order', 'id')
        )
        
        #移動区間を区間順に表示
        sections = list(
            log.sections
            .select_related('from_spot', 'to_spot')
            .order_by('section_order', 'id')
        )
        
        # 保存されている分を、表示用の「時間・分」に変換
        for section in sections:
            if section.duration is None:
                section.duration_display = '未設定'
            else:
                hours, minutes = divmod(section.duration, 60)
                
                if hours and minutes:
                    section.duration_display = f'{hours}時間{minutes}分'
                elif hours:
                    section.duration_display = f'{hours}時間'
                else:
                    section.duration_display = f'{minutes}分'

        
        #移動区間とその直後に表示するカードを組み合わせる
        context['timeline'] = [
            {
                'section': section,
                'card': card}
            for section, card in zip_longest(sections, cards)
        ]
        
        #ログのユーザーが自分自身かどうかを判定
        context['is_owner'] = (
            log.user_id == self.request.user.pk
        )
        
        return context
