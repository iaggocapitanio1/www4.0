from rest_framework.routers import DefaultRouter
from rest_framework.urls import path
from . import views

app_name = 'users'
namespace = app_name
router = DefaultRouter()

router.register("organization", views.OrganizationViewSet, basename="organization")
router.register("worker", views.WorkerViewSet, basename="worker")
router.register("customer", views.CustomerViewSet, basename="customer")
router.register("address", views.AddressView, basename="address")
urlpatterns = [
    path('get-customer/', views.GetCustomerAPIView.as_view(), name='get-customer'),
    path('signup/', views.SignupView.as_view(), name='register'),
    path('reset-password', views.ResetPasswordView.as_view(), name='reset-password'),
    path('reset-password/<uidb64>/<token>', views.SetNewPassword.as_view(), name='reset-password-new'),
    path("activate/<uidb64>/<token>", views.ActivateUserView.as_view(), name='activate'),
    path("reactivate", views.ResendActivation.as_view(), name="reactivate")

]
urlpatterns += router.urls
