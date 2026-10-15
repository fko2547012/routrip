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
                for card_form in formset.initial_forms:
                    card = card_form.instance
                    key = (prev_spot_id, card.spot_id)
                    
                    section = (
                        sections[key].popleft()
                        if sections[key]
                        else None
                        )
                    if section:
                        card_form.initial["transport"] = section.transport
                        card_form.initial["duration"] = section.duration
                        
                        # 保存済みの時間が選択肢にない場合は追加する
                        duration_field = card_form.fields["duration"]
                        choices = list(duration_field.choices)
                        
                        if (
                            section.duration is not None
                            and section.duration not in [
                                value for value, _ in choices
                                ]
                            ):
                            choices.append(
                                (section.duration, f"{section.duration}分")
                                )
                            duration_field.choices = choices
                            prev_spot_id = card.spot_id
                            return formset
                        
    def get_context_data(self, **kwargs):
        #カード・写真・サムネイルの情報をHTMLへ渡す。
        context = super().get_context_data(**kwargs)
        if "formset" not in context:
            context["formset"] = self.get_formset()
            saved_cards = {
                card.pk: card
                for card in self.object.cards.all()}
            
            images = {}
            thumbnail = ""
            for card_form in context["formset"].initial_forms:
                card = saved_cards.get(card_form.instance.pk)
                if card and card.image_path:
                    images[card_form.prefix] = card.image_path.url
                    if card and card.pk == self.object.thumbnail_card_id:
                        thumbnail = card_form.prefix
                        context["card_images"] = images
                        context["selected_thumbnail"] = (self.request.POST.get("thumbnail", "")
                                                        if self.request.method == "POST"
                                                        else thumbnail)
                        return context
                    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        
        #ログとカードを検証し、まとめて保存する, 保存に失敗した場合はDBの変更を取り消す
        self.object = self.get_object()

        # 変更前に使用していたスポットを記録する
        self.old_spot_ids = {self.object.start_spot_id}

        self.old_spot_ids.update(
            self.object.cards.values_list("spot_id", flat=True)
        )

        for from_id, to_id in self.object.sections.values_list(
            "from_spot_id", "to_spot_id"
        ):
            self.old_spot_ids.update((from_id, to_id))

        form = self.get_form()
        self.formset = self.get_formset()

        # 両方のエラーを画面に表示できるように検証する
        form_valid = form.is_valid()
        formset_valid = self.formset.is_valid()

        if form_valid and formset_valid:
            return self.form_valid(form)

        return self.render_to_response(
            self.get_context_data(
                form=form,
                formset=self.formset,
            )
        )

                    
                
    def get_success_url(self):
        #ログ詳細画面にリダイレクトする
        return reverse('routrip:log_detail', kwargs={'pk': self.object.pk})