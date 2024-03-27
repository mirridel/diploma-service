from django.urls import path, re_path

from car_service.apps.services import views

app_name = 'services'
urlpatterns = [
    path('', views.ServiceList.as_view(), name='index'),
    path('booking/', views.booking, name='booking'),
    path('booking/<slug:slug>/', views.booking, name='booking'),
    re_path(r'^car-autocomplete/$', views.CarAutocomplete.as_view(), name='car-autocomplete'),
]
