from django.urls import path
from .views import MHFFilterView, HomePageView, UserLoginView, UserLogoutView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),  # Home page view
    path('mhpfilter/', MHFFilterView.as_view(), name='mhpfilter'),  # MHF Filter view
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
