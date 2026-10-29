from django import forms
from django.forms import inlineformset_factory
from routrip.forms.log import LogCardFormSet
from ..models import Log, Logcard
from django.forms import BaseInlineFormSet

class EditCardForm(LogCardFormSet.form):
    """
    共通フォームを引継ぐ
    """
    pass


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