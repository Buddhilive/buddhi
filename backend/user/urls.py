from django.urls import path
from .views import UserInfoView, UserLogoutView, UserRegistrationView, UserLoginView

urlpatterns = [
    path('info/', UserInfoView.as_view(), name='user-info'),
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
]