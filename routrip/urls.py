from django.urls import path
from .views.top_page import TopPageView

app_name = 'routrip'
urlpatterns = [
    path('', TopPageView.as_view(), name='top_page')
]