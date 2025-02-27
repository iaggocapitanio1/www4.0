from django.contrib import admin
from django.urls import path, include
from entities.views import HomeView
from django.conf import settings

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('auth/', include('drf_social_oauth2.urls', namespace='drf')),
    path('api/v1/chat/', include('chat.urls')),
    path('api/v1/perms/', include('permissions.urls')),
    path('api/v1/accounts/', include('users.urls')),
    path("api/v1/email/", include("emailManager.urls")),
    path("api/v1/", include('entities.urls')),
    path("api/v1/", include('tags.urls')),
    path("api/v1/storages/", include('bucket.urls')),
    path("protected/", include('protected_media.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path('api-auth/', include('rest_framework.urls')),
        path('admin/', admin.site.urls),
    ]
