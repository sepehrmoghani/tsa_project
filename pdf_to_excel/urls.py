from django.urls import path
from .views import PdfToExcelView, HomePageView, UserLoginView, UserLogoutView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),  # Home page view
    path('pdf_to_excel/', PdfToExcelView.as_view(), name='pdf_to_excel'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
