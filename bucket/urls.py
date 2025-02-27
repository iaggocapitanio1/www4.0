from rest_framework.routers import DefaultRouter
from rest_framework.urls import path
from . import views

app_name = 'storages'
namespace = app_name
router = DefaultRouter()

router.register("folder", views.FolderViewSet, basename="folder")
router.register("file", views.FileViewSet, basename="file")
router.register("leftover", views.LeftOverImageViewSet, basename="leftover")
# router.register("cut-list", views.FurnitureCutListViewSet, basename="cut-list")
# router.register("easm", views.EASMViewSet, basename="easm")
urlpatterns = router.urls
urlpatterns += [path('error/', views.ErrorFile.as_view(), name='error')]
