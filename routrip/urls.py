from django.urls import path
from .views.account import SignUpView,CustomLoginView,CustomLogoutView
from .views.log_list import LogListView
from .views.mypage import MypageView
from .views.log_create import LogCreateView
from .views.log_detail import LogDetailView
from .views.log_edit import LogUpdateView
from .views.log_delete import LogDeleteView
from .views.spot import search_spots, nearby_spots, suggest_spots

app_name = 'routrip'
urlpatterns = [
    path('', LogListView.as_view(), name='top_page'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('log/list/', LogListView.as_view(), name='log_list'),
    path('mypage/', MypageView.as_view(), name='mypage'),
    path('log_create/', LogCreateView.as_view(), name='log_create'),
    path('log_detail/<int:pk>/', LogDetailView.as_view(), name='log_detail'),
    path('log_edit/<int:pk>/', LogUpdateView.as_view(), name='log_edit'),
    path('log_delete/<int:pk>/', LogDeleteView.as_view(), name='log_delete'),
    path('log/create/', LogCreateView.as_view(), name='log_create'),
    path('spots/search/', search_spots, name='search_spots'),
    path('spots/nearby/', nearby_spots, name='nearby_spots'),
    path('spots/suggest/', suggest_spots, name='suggest_spots')
]