from rest_framework import permissions
class HasWW4Scope(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        if request.auth:
            return "ww4" in request.auth.scopes
        return False
