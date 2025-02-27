from rest_framework import permissions
from .functions import flat_list, generate_perms
from .constants import RESOURCES
from .decorators import check_api_connection
from rest_framework.permissions import DjangoModelPermissions

methods = None


def work_perms() -> list:
    """
    The goal of this function is to generate the worker permissions.
    :return:
    """
    tmp = list()
    for resource in RESOURCES:
        actions = None
        if resource == 'organization':
            actions = ['view']
        tmp.extend(generate_perms(resource, methods=actions))
    return tmp


def customer_perms() -> list:
    """
   The goal of this function is to generate the customer permissions.
   :return:
   """
    tmp = list()
    for resource in RESOURCES:
        actions = []
        if resource == ['project', 'expedition', 'budget']:
            actions = ['view']
        elif resource == 'owner':
            actions = None
        tmp.extend(generate_perms(resource, methods=actions))
    return tmp


class ModelPermissions(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class GetCustomerIDPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == "POST" and request.user is None or request.user.is_customer:
            return True
        else:
            return False


class HasConnection(permissions.BasePermission):

    @check_api_connection
    def has_permission(self, request, view):
        return True


class WorkPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.has_perm('create_permission') or request.user.has_perm("permissions.add_permission")
        elif view.action == "list":
            return request.user.has_perm("view_permission") or request.user.has_perm("permissions.view_permission")
        elif view.action == "retrieve":
            return request.user.has_perm("view_permission") or request.user.has_perm("permissions.view_permission")
        elif view.action == "update":
            return request.user.has_perm("change_permission") or request.user.has_perm("permissions.change_permission")
        elif view.action == "partial_update":
            return request.user.has_perm("change_permission") or request.user.has_perm("permissions.change_permission")
        elif view.action == "destroy":
            return request.user.has_perm("delete_permission") or request.user.has_perm("permissions.delete_permission")


class PermissionPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.has_perm('create_permission') or request.user.has_perm("permissions.add_permission")
        elif view.action == "list" or view.action == "no_pagination":
            return request.user.has_perm("view_permission") or request.user.has_perm("permissions.view_permission")
        elif view.action == "retrieve":
            return request.user.has_perm("view_permission") or request.user.has_perm("permissions.view_permission")
        elif view.action == "update":
            return request.user.has_perm("change_permission") or request.user.has_perm("permissions.change_permission")
        elif view.action == "partial_update":
            return request.user.has_perm("change_permission") or request.user.has_perm("permissions.change_permission")
        elif view.action == "destroy":
            return request.user.has_perm("delete_permission") or request.user.has_perm("permissions.delete_permission")
        elif view.action == 'orion_permissions':
            return request.user.has_perm('permissions.view_permission')
        elif view.action == 'orion_permissions_put':
            return request.user.has_perm('permissions.change_permission')
        elif view.action == 'orion_permissions_delete':
            return request.user.has_perm('permissions.delete_permission')


class GroupPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.has_perm('create_group') or request.user.has_perm('permissions.add_group')
        elif view.action == "list" or view.action == "no_pagination":
            return True  # request.user.has_perm("view_group")
        elif view.action == "expanded":
            return request.user.has_perm("view_group") or request.user.has_perm('permissions.view_group')
        elif view.action == "retrieve":
            return request.user.has_perm("view_group") or request.user.has_perm('permissions.view_group')
        elif view.action == "update":
            return request.user.has_perm("change_group") or request.user.has_perm('permissions.change_group')
        elif view.action == "partial_update":
            return request.user.has_perm("change_group") or request.user.has_perm('permissions.change_group')
        elif view.action == "destroy":
            return request.user.has_perm("delete_group") or request.user.has_perm('permissions.delete_group')
        elif view.action == 'orion_groups':
            return request.user.has_perm('permissions.view_group')
        elif view.action == 'orion_groups_put':
            return request.user.has_perm('permissions.change_group')
        elif view.action == 'orion_groups_delete':
            return request.user.has_perm('permissions.delete_group')


class EmailPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_admin or request.user.is_worker


class IsResourceOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user


class CanChangeActivation(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.has_perm('can_active')


ADMIN_PERMISSIONS = flat_list([generate_perms(resource=resource) for resource in RESOURCES])

WORKER_PERMISSIONS = work_perms()

CUSTOMER_PERMISSIONS = customer_perms()
