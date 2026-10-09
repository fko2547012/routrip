from django import forms
from django.forms import ModelForm
from django.forms import inlineformset_factory
from ..models import Log, Logcard
import re


class LogForm(ModelForm):
    '''
    ログ投稿フォーム
    '''
    tag_text=forms.CharField(
        label='タグ',
        required=False,
        help_text='スペースまたはカンマで区切ってタグを入力してください')

    class Meta:
        model = Log
        fields = ['title', 'trip_start_date', 'trip_end_date', 'start_spot']
        widgets = {
            'trip_start_date': forms.DateInput(attrs={'type': 'date'}),
            'trip_end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('trip_start_date')
        end = cleaned.get('trip_end_date')
        if start and end and end < start:
            raise forms.ValidationError('終了日は開始日以降にしてください')
        return cleaned

    def clean_tag_text(self):
        '''
        タグの入力値をチェック
        return: タグのリスト
        '''
        text = self.cleaned_data['tag_text']
        names = []
        for name in re.split(r'[,\s、，]+', text):  #カンマ・スペース・読点で分割
            if name and name not in names:  #空文字と重複を除く
                names.append(name)
        for name in names:  #30文字以内かどうかをチェック
            if len(name) > 30:
                raise forms.ValidationError('タグは30文字以内にしてください')
        return names  


LogCardFormSet = inlineformset_factory( #カードを複数枚作成するフォームセット
    Log, Logcard,
    fields=['spot', 'image_path', 'comment'],
    extra=3,    #カードを3枚表示
    can_delete=False,
)