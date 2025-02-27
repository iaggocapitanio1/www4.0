from django.conf import settings

if not hasattr(settings, "PROTECTED_MEDIA_ROOT") and not hasattr(settings, "BASE_DIR"):
    raise RuntimeError("The default value for PROTECTED_MEDIA_ROOT requires BASE_DIR to be an available setting.")

PROTECTED_MEDIA_ROOT = getattr(
    settings, "PROTECTED_MEDIA_ROOT", "%s/protected/" % settings.BASE_DIR 
)

PROTECTED_MEDIA_URL = getattr(
    settings, "PROTECTED_MEDIA_URL", "/protected/"
)

PROTECTED_MEDIA_LOCATION_PREFIX = getattr(
    settings, "PROTECTED_MEDIA_LOCATION_PREFIX", PROTECTED_MEDIA_URL
)

PROTECTED_MEDIA_SERVER = getattr(
    settings, "PROTECTED_MEDIA_SERVER", "django"
)

PROTECTED_MEDIA_AS_DOWNLOADS = False

