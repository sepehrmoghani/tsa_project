# tsa_project.urls
from django.contrib import admin
from django.urls import path, include
from pdf_to_excel.views import HomePageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pdf_to_excel/', include('pdf_to_excel.urls')),
    path('fileprocessor/', include('fileprocessor.urls')),
    path('mhpfilter/', include('mhpfilter.urls')),
    path('gmaps_distance/', include('gmaps_distance.urls')),
    path('startrack_convert/', include('StartrackConvert.urls')),
    path('status_lookup/', include('StatusLookup.urls')),
    path('', HomePageView.as_view(), name='home'),  # Home page view
]
