from django.urls import path
from .views import GmapsdistanceView, HomePageView, UserLoginView, UserLogoutView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('gmaps_distance/', GmapsdistanceView.as_view(), name='gmaps_distance'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
