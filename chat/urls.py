from rest_framework.routers import DefaultRouter

from . import views

app_name = 'chat'
namespace = app_name
router = DefaultRouter()
router.register("message", views.MessageViewSet, basename="message")

urlpatterns = router.urls
