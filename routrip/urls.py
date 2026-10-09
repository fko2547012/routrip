from django.urls import path
from .views.top_page import TopPageView
from .views.account import SignUpView,CustomLoginView,CustomLogoutView
from .views.log_list import LogListView
from .views.mypage import MypageView
from .views.log_create import LogCreateView

app_name = 'routrip'
urlpatterns = [
    path('', TopPageView.as_view(), name='top_page'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('log_list/', LogListView.as_view(), name='log_list'),
    path('mypage/', MypageView.as_view(), name='mypage'),
    path('log_create/', LogCreateView.as_view(), name='log_create')
]