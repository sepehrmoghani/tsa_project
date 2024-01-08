from django.urls import path
from .views import StatusLookupView, HomePageView, UserLoginView, UserLogoutView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),  # Home page view
    path('StatusLookup/', StatusLookupView.as_view(), name='StatusLookup'),  # MHF Filter view
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
