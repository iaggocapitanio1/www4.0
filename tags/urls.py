from rest_framework.routers import DefaultRouter
from tags import views

app_name = 'tags'
namespace = app_name
router = DefaultRouter()

router.register("tag", views.TagsViewSet, basename="tag")
router.register("tag-result", views.TagsResultViewSet, basename="tag-result")
urlpatterns = router.urls
