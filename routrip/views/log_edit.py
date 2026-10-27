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


class BaseEditCardFormSet(BaseInlineFormSet):
    """
    カードの並び順と削除状態を管理する。
    """
    ordering_widget = forms.HiddenInput
    deletion_widget = forms.HiddenInput

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        # 編集対象以外のカードが送信されていないか確認
        expected_ids = set(
            self.get_queryset().values_list("pk", flat=True)
        )

        submitted_ids = [
            form.cleaned_data["id"].pk
            for form in self.initial_forms
            if form.cleaned_data.get("id")
        ]

        if (
            len(submitted_ids) != len(expected_ids)
            or set(submitted_ids) != expected_ids or any(form.cleaned_data.get("id")
                for form in self.extra_forms
            )
        ):
            raise forms.ValidationError("カード情報を確認できません。画面を開き直してください。")

        # 削除しないカードの表示順を確認
        orders = []
        for form in self.forms:
            if self._should_delete_form(form):
                continue
            if not form.instance.pk and not form.has_changed():
                continue
            
            order = form.cleaned_data.get("ORDER")
            if order is None or order < 1:
                raise forms.ValidationError("カードの表示順を確認してください。")
            
            orders.append(order)
            if len(orders) != len(set(orders)):
                raise forms.ValidationError("カードの表示順が重複しています。")


class EditCardForm(LogCardFormSet.form):
    """
    移動時間の単位を選択できる編集用フォーム。
    """

    duration_unit = forms.ChoiceField(
        label="単位",
        choices=[
            ("minutes", "分"),
            ("hours", "時間"),
        ],
        initial="minutes",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["image_path"].widget = forms.FileInput(
            attrs={"accept": "image/*"}
        )

        self.fields["duration"].label = "移動時間"
        self.fields["duration"].widget.attrs["placeholder"] = "移動時間"

    def clean(self):
        cleaned = super().clean()

        duration = cleaned.get("duration")
        unit = cleaned.get("duration_unit") or "minutes"

        if duration is not None:
            # DBには分で保存する
            if unit == "hours":
                duration *= 60

            if duration > 14400:
                self.add_error(
                    "duration",
                    "移動時間は240時間以内で入力してください。",
                )
            else:
                cleaned["duration"] = duration
        return cleaned


# 作成時と同じカードフォームを使用する, 編集では並び替えと削除を有効にする
EditCardFormSet = inlineformset_factory(
    Log,
    Logcard,
    form=EditCardForm,
    formset=BaseEditCardFormSet,
    extra=0,
    min_num=1,
    validate_min=True,
    can_order=True,
    can_delete=True,
)


class LogUpdateView(LoginRequiredMixin, UpdateView):
    """
    ログ編集ビュー。
    投稿者本人のログ・カード・移動区間・タグを更新する。
    """
    model = Log
    form_class = LogForm
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
            
            saved_cards = {
            card.pk: card
            for card in self.object.cards.all()
        }
            
            images = {}
            thumbnail = ""
            
            for card_form in context["formset"].initial_forms:
                card = saved_cards.get(card_form.instance.pk)
                
                if card and card.image_path:
                    images[card_form.prefix] = card.image_path.url
                    
                    if card and card.pk == self.object.thumbnail_card_id:
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

        self.old_spot_ids = {self.object.start_spot_id}

        self.old_spot_ids.update(
            self.object.cards.values_list("spot_id", flat=True)
        )

        for from_id, to_id in self.object.sections.values_list("from_spot_id", "to_spot_id"):
            self.old_spot_ids.update((from_id, to_id))

        form = self.get_form()
        self.formset = self.get_formset()

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

        # 変更していない既存カードも含めて保存する
        for order, card_form in enumerate(
            self.formset.ordered_forms,
            start=1,
        ):
            card = card_form.save(commit=False)
            card.log = self.object
            card.display_order = order

            # 写真を変更した場合、古い撮影情報を消す
            if "image_path" in card_form.changed_data:
                card.taken_at = None
                card.latitude = None
                card.longitude = None
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

        # どこからも参照されていないものだけ削除する
        Spot.objects.filter(
            pk__in=self.old_spot_ids,
            start_logs__isnull=True,
            log_cards__isnull=True,
            departing_sections__isnull=True,
            arriving_sections__isnull=True,
        ).delete()

        messages.success(self.request, "ログを更新しました。")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """
        更新したログの詳細画面へ戻る。
        """
        return reverse(
            "routrip:log_detail",
            kwargs={"pk": self.object.pk},
        )