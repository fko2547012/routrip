from django import forms
from ..models import Spot


class SpotForm(forms.ModelForm):
    class Meta:
        model = Spot
        fields = [
            "name",
            "latitude",
            "longitude",
        ]

        labels = {
            "name": "スポット名",
            "latitude": "緯度",
            "longitude": "経度",
        }

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "スポット名を入力してください",
            }),
            "latitude": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "any",
                "placeholder": "緯度",
            }),
            "longitude": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "any",
                "placeholder": "経度",
            }),
        }