from django.urls import path
from .views import ConnoteCompareView, HomePageView, UserLoginView, UserLogoutView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),  # Home page view
    path('fileprocessor/', ConnoteCompareView.as_view(), name='fileprocessor'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
