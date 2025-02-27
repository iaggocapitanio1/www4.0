from rest_framework.routers import DefaultRouter
from rest_framework.urls import path
from . import views

app_name = 'email'
namespace = app_name

urlpatterns = [
    path('service/', views.SendEmailViewSet.as_view(), name='service'),

]
