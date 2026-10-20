from django.views import View
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from ..models import Log, Tag, Section, Spot
from ..forms.log import LogForm, LogCardFormSet
from ..utils.photo import get_photo_info
from ..utils.spot import haversine_m


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
        saved_cards = {}
        new_spots = []
        for index, card_form in enumerate(formset.forms):
            if not card_form.has_changed(): # 何も入力されていない欄は無視
                continue
            order += 1
            card = card_form.save(commit=False)
            card.log = self.object
            card.display_order = order

            new_name = card_form.cleaned_data.get('new_spot_name')
            if new_name:
                card.spot = self.get_new_spot(
                    new_name,
                    card_form.cleaned_data['new_spot_lat'],
                    card_form.cleaned_data['new_spot_lng'],
                    new_spots) 

            photo = card_form.cleaned_data.get('image_path')
            if photo:
                info = get_photo_info(photo)
                card.taken_at = info['taken_at']
                card.latitude = info['lat']
                card.longitude = info['lng'] 

            card.save() # カードを保存
            saved_cards[index] = card  # 保存したカードを記録

            Section.objects.create( # 手前の移動区間を保存
                log=self.object,
                from_spot=prev_spot,
                to_spot=card.spot,
                section_order=order,
                transport=card_form.cleaned_data['transport'],
                duration=card_form.cleaned_data['duration'],
            )
            prev_spot = card.spot   # 次のカードの出発側にする

        value = self.request.POST.get('thumbnail', '')
        thumb_card = saved_cards.get(int(value)) if value.isdigit() else None
        if thumb_card is None:                                  # 選ばれていなければ、最初の写真のカード
            thumb_card = next(
                (c for c in saved_cards.values() if c.image_path), None)
        self.object.thumbnail_card = thumb_card
        self.object.save(update_fields=['thumbnail_card'])

        
        return response

    def get_new_spot(self, name, lat, lng, created):
        """
        新しいスポットを作る。
        この投稿の中で、同じ名前で100m以内のスポットを、すでに作っていたら、それを使う。
        """
        for spot in created:
            if spot.name == name and haversine_m(spot.latitude, spot.longitude, lat, lng) <= 100:
                return spot
        spot = Spot.objects.create(
            name=name, latitude=lat, longitude=lng,
            registered_user=self.request.user)
        created.append(spot)
        return spot

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