from django import forms
from django.forms import inlineformset_factory
from routrip.forms.log import LogCardFormSet, LogForm
from ..models import Log, Logcard
from django.forms import BaseInlineFormSet

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

        self.fields["spot"].widget = forms.Select(
            choices=self.fields["spot"].choices
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
class BaseEditCardFormSet(BaseInlineFormSet):
    """
    カードの並び替えと削除を管理するフォームセット
    """
    ordering_widget = forms.HiddenInput
    deletion_widget = forms.HiddenInput

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        orders = []

        for form in self.forms:
            if self._should_delete_form(form):
                continue

            if not form.instance.pk and not form.has_changed():
                continue

            order = form.cleaned_data.get("ORDER")

            if order is None or order < 1:
                raise forms.ValidationError(
                    "カードの表示順を確認してください。"
                )

            if order in orders:
                raise forms.ValidationError(
                    "カードの表示順が重複しています。"
                )

            orders.append(order)
            
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


class EditLogForm(LogForm):
    """
    編集画面に出発地の選択欄を表示する。
    """
    class Meta(LogForm.Meta):
        fields = [
            "title",
            "trip_start_date",
            "trip_end_date",
            "start_spot",
        ]
        