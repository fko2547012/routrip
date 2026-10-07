from django.urls import path
from .views.top_page import TopPageView
from .views.signup import SignUpView

app_name = 'routrip'
urlpatterns = [
    path('', TopPageView.as_view(), name='top_page'),
    path('signup/', SignUpView.as_view(), name='signup'),
]