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
        error_messages = {
            'title': {'required': 'タイトルを入力してください'},
            'trip_start_date': {'required': '開始日を入力してください'},
            'trip_end_date': {'required': '終了日を入力してください'},
        }
                

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('trip_start_date')
        end = cleaned.get('trip_end_date')
        if start and end and end < start:
            self.add_error('trip_end_date', '終了日は開始日以降にしてください')
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


TRANSPORT_CHOICES = [
    ('徒歩', '徒歩'), ('電車', '電車'), ('バス', 'バス'), ('車', '車'),
    ('自転車', '自転車'), ('飛行機', '飛行機'), ('船', '船'),
]

DURATION_CHOICES = [(m, f'{m}分') for m in (10, 20, 30, 45, 60, 90, 120, 180)]   # 仮


class LogCardForm(ModelForm):
    '''
    カード1枚分のフォーム（手前の移動手段・移動時間を含む）
    '''
    transport = forms.ChoiceField(
        label='移動手段',
        choices=[('', '選択してください')] + TRANSPORT_CHOICES,
        error_messages={'required': '移動手段を選択してください'})
    duration = forms.TypedChoiceField(
        label='移動時間', required=False,
        choices=[('', '----')] + DURATION_CHOICES,
        coerce=int, empty_value=None)

    field_order = ['transport', 'duration', 'spot', 'image_path', 'comment']

    class Meta:
        model = Logcard
        fields = ['spot', 'image_path', 'comment']
        error_messages = {
            'spot': {'required': 'スポットを入力してください'},
            'comment': {'required': 'コメントを入力してください'},
        }


LogCardFormSet = inlineformset_factory(
    Log, Logcard,
    form=LogCardForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=False,
)