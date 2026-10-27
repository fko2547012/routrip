from django import forms
from django.forms import ModelForm
from django.forms import inlineformset_factory
from ..models import Log, Logcard, Spot
import re


class LogForm(ModelForm):
    '''
    ログ投稿フォーム
    '''
    tag_text = forms.CharField(
        label='タグ',
        required=False,
        widget=forms.HiddenInput)

    class Meta:
        model = Log
        fields = ['title', 'trip_start_date', 'trip_end_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'タイトル入力'}),
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


class LogCardForm(ModelForm):
    '''
    カード1枚分のフォーム（手前の移動手段・移動時間を含む）
    '''
    transport = forms.ChoiceField(
        label='移動手段',
        choices=[('', '選択してください')] + TRANSPORT_CHOICES,
        error_messages={'required': '移動手段を選択してください'})
    duration = forms.IntegerField(
        label='移動時間（分）',
        required=False,
        min_value=1,
        max_value=14400,      
        widget=forms.NumberInput(attrs={
            'placeholder': '移動時間（分）',
            'inputmode': 'numeric',    # スマホで数字のキーボードを出す
        }),
        error_messages={
            'invalid': '移動時間は数字で入力してください',
            'min_value': '移動時間は1分以上で入力してください',
            'max_value': '移動時間が長すぎます',
        })

    new_spot_name = forms.CharField(
        required=False, max_length=30,      # Spot.name の max_length に合わせる
        widget=forms.TextInput(attrs={'placeholder': '新しい場所の名前を入力'}))
    new_spot_lat = forms.FloatField(
        required=False, min_value=-90, max_value=90, widget=forms.HiddenInput)
    new_spot_lng = forms.FloatField(
        required=False, min_value=-180, max_value=180, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['spot'].required = False     # 新しい場所のときは、空でもよい

    def clean(self):
        cleaned = super().clean()
        name = (cleaned.get('new_spot_name') or '').strip()

        if name:
            if cleaned.get('new_spot_lat') is None or cleaned.get('new_spot_lng') is None:
                self.add_error('new_spot_name', '位置情報を取得できませんでした。既存のスポットを選んでください')
            else:
                cleaned['new_spot_name'] = name
                cleaned['spot'] = None            # 新しい場所を使う
        elif not cleaned.get('spot'):
            self.add_error('spot', 'スポットを入力してください')
        return cleaned

    field_order = ['transport', 'duration', 'spot', 'image_path', 'comment']
    spot_label = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Logcard
        fields = ['spot', 'image_path', 'comment']
        widgets = {'spot': forms.HiddenInput}   # 画面に戻すときの、表示用の名前
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

class StartSpotForm(forms.Form):
    '''
    出発地のフォーム（カードのスポット欄と同じ仕組み）
    '''
    spot = forms.ModelChoiceField(
        queryset=Spot.objects.all(), required=False, widget=forms.HiddenInput)
    spot_label = forms.CharField(required=False, widget=forms.HiddenInput)
    new_spot_name = forms.CharField(
        required=False, max_length=30,
        widget=forms.TextInput(attrs={'placeholder': '新しい場所の名前を入力'}))
    new_spot_lat = forms.FloatField(
        required=False, min_value=-90, max_value=90, widget=forms.HiddenInput)
    new_spot_lng = forms.FloatField(
        required=False, min_value=-180, max_value=180, widget=forms.HiddenInput)

    def clean(self):
        cleaned = super().clean()
        name = (cleaned.get('new_spot_name') or '').strip()

        if name:
            if cleaned.get('new_spot_lat') is None or cleaned.get('new_spot_lng') is None:
                self.add_error('new_spot_name', '位置情報を取得できませんでした。もう一度、検索してください')
            else:
                cleaned['new_spot_name'] = name
                cleaned['spot'] = None
        elif not cleaned.get('spot'):
            self.add_error('spot', '出発地を入力してください')
        return cleaned