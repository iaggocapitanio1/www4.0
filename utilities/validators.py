import re
from django.core.validators import ValidationError


def validate_filesystem_path(value):
    if re.search(r'[?*:\\]', value):
        raise ValidationError("Path contains invalid characters (?, *, or :).")
