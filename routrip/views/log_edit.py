from collections import defaultdict, deque

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..models import Log, Tag, Section, Spot
from ..forms.log import EditLogForm, EditCardFormSet

        
class LogUpdateView(LoginRequiredMixin, UpdateView):
    """
    ログ編集ビュー
    """
    model = Log
    form_class = EditLogForm
    template_name = "routrip/log_edit.html"
    context_object_name = "log"
    login_url = "routrip:login"

    def get_queryset(self):
        """
        自分が投稿したログだけ取得する。
        """
        queryset = super().get_queryset().filter(user=self.request.user)

        if self.request.method == "POST":
            queryset = queryset.select_for_update()
            
        return queryset

    def get_initial(self):
        """
        登録済みのタグをフォームに入れる。
        """
        initial = super().get_initial()
        
        initial["tag_text"] = " ".join(self.object.tags.values_list("name", flat=True))
        return initial
    
    def get_form(self, form_class=None):
        """
        登録済みの日付を日付入力欄に表示する。
        """
        form = super().get_form(form_class)
        for name in ("trip_start_date", "trip_end_date"):
            form.fields[name].widget = forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            )
        return form
        
    def get_formset(self):
        """
        登録済みのカードと移動情報を読み込む。
        """
        kwargs = {
            "instance": self.object,
            "prefix": "cards",
            "queryset": self.object.cards.order_by(
                "display_order", "id"
            ),
        }

        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
            
        formset = EditCardFormSet(**kwargs)
        """
        出発・到着スポットごとに移動区間をまとめる
        """
        sections = defaultdict(deque)

        for section in self.object.sections.order_by("section_order", "id"):
            key = (section.from_spot_id, section.to_spot_id)
            sections[key].append(section)

        prev_spot_id = self.object.start_spot_id

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
                duration = section.duration
                if (
                    duration is not None
                    and duration > 0
                    and duration % 60 == 0
                ):
                    card_form.initial["duration"] = duration // 60
                    card_form.initial["duration_unit"] = "hours"
                else:
                    card_form.initial["duration"] = duration
                    card_form.initial["duration_unit"] = "minutes"
            prev_spot_id = card.spot_id
        return formset

    def get_context_data(self, **kwargs):
        """
        カード・写真・サムネイルの情報をHTMLへ渡す。
        """
        context = super().get_context_data(**kwargs)
        if "formset" not in context:
            context["formset"] = self.get_formset()
            
            images = {}
            thumbnail = ""
            
            for card_form in context["formset"].initial_forms:
                card = card_form.instance
                
                if card.image_path:
                    images[card_form.prefix] = card.image_path.url
                    
                    if card.pk == self.object.thumbnail_card_id:
                        thumbnail = card_form.prefix

        context["card_images"] = images

        context["selected_thumbnail"] = (
            self.request.POST.get("thumbnail", "")
            if self.request.method == "POST"
            else thumbnail
        )

        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        ログとカードを検証して、まとめて更新する。
        """
        self.object = self.get_object()
        
        form=self.get_form()
        self.formset=self.get_formset()

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

    def form_valid(self, form):
        """
        ログ・カード・移動区間・タグを保存する。
        """
        self.object = form.save(commit=False)

        # カードを削除する前にサムネイルの参照を外す
        self.object.thumbnail_card = None
        self.object.save()
        form.save_m2m()

        # 移動区間は変更後のカード順で作り直す
        self.object.sections.all().delete()

        # 削除指定されたカードを削除
        for card_form in self.formset.deleted_forms:
            if card_form.instance.pk:
                card_form.instance.delete()

        prev_spot = self.object.start_spot
        saved_cards = {}
        new_spots=[]

        # 変更していない既存カードも含めて保存する
        for order, card_form in enumerate(
            self.formset.ordered_forms,
            start=1,
        ):
            card = card_form.save(commit=False)
            card.log = self.object
            card.display_order = order
            
        # 新しいスポットを登録
        new_name = card_form.cleaned_data.get(
            "new_spot_name"
        )
        if new_name:
            card.spot = self.get_new_spot(
                new_name,
                card_form.cleaned_data["new_spot_lat"],
                card_form.cleaned_data["new_spot_lng"],
                new_spots,
            )
        
        # 写真変更時はEXIF情報を更新
        if "image_path" in card_form.changed_data:
            photo = card_form.cleaned_data.get(
                "image_path"
            )
            if photo:
                info = get_photo_info(photo)
                card.taken_at = info["taken_at"]
                card.latitude = info["lat"]
                card.longitude = info["lng"]
            else:
                card.taken_at = None
                card.latitude = None
                card.longitude = None

        # カードを保存
        card.save()
        card_form.save_m2m()

        saved_cards[card_form.prefix] = card

        # カードの手前の移動区間を保存
        Section.objects.create(
            log=self.object,
            from_spot=prev_spot,
            to_spot=card.spot,
            section_order=order,
            transport=card_form.cleaned_data["transport"],
            duration=card_form.cleaned_data["duration"],
        )
            
        prev_spot = card.spot

        # タグを現在の入力内容に置き換える
        tags = []
        for name in form.cleaned_data["tag_text"]:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)

        self.object.tags.set(tags)

        # サムネイルを保存
        value = self.request.POST.get("thumbnail", "")
        thumb_card = saved_cards.get(value)

        if thumb_card is None or not thumb_card.image_path:
            thumb_card = next(
                (card for card in saved_cards.values()
                    if card.image_path
                ),
                None,
            )

        self.object.thumbnail_card = thumb_card
        self.object.save(update_fields=["thumbnail_card"])
        
        messages.success(
            self.request,
            "ログを更新しました。"
        )

        return HttpResponseRedirect(
            self.get_success_url()
        )
        
    def get_new_spot(self, name, lat, lng, created):
        """
        新しいスポットを作る。
        同じ投稿内で名前が同じかつ100m以内なら再利用する。
        """
        for spot in created:
            if (
                spot.name == name
                and haversine_m(
                    spot.latitude,
                    spot.longitude,
                    lat,
                    lng
                ) <= 100
            ):
                return spot

        spot = Spot.objects.create(
            name=name,
            latitude=lat,
            longitude=lng,
            registered_user=self.request.user,
        )

        created.append(spot)

        return spot


    def get_success_url(self):
        """
        更新したログの詳細画面へ戻る。
        """
        return reverse(
            "routrip:log_detail",
            kwargs={"pk": self.object.pk},
        )