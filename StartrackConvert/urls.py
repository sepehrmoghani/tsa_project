from django.urls import path
from .views import StartrackInvoiceConvertView, HomePageView, UserLoginView, UserLogoutView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('StartrackConvert/', StartrackInvoiceConvertView.as_view(), name='StartrackConvert'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
