from rest_framework.routers import DefaultRouter
from rest_framework.urls import path
from . import views

app_name = 'permissions'
namespace = app_name
router = DefaultRouter()

router.register("permission", views.PermissionsViewSet, basename="permission")
router.register("group", views.GroupViewSet, basename="group")
router.register(r'group-management', views.GroupManagerViewSet, basename="group-management")
urlpatterns = router.urls
