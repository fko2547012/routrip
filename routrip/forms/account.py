from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm

User=get_user_model()

class SignUpForm(UserCreationForm):
    

    class Meta(UserCreationForm.Meta):
        model=User
        fields=("username",)

class LoginForm(AuthenticationForm):
    #ログインフォーム
    username=forms.CharField(
        label="ユーザー名",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ユーザー名を入力してください',

        })
        )
    password=forms.CharField(
            label='パスワード',
            widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'パスワードを入力してください',
            })
        )