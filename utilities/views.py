from django.urls import reverse
from rest_framework import views, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from permissions.serializers import AddPermissionsSerializer, AddGroupSerializer, DjangoUserGroupSerializer, \
    DjangoUserGroupSerializerRead
from users.models import User
from utilities.constants import FurnitureType
from utilities.decorators import user_has_orion_permission, customer_profile_exists
from utilities.functions import generate_urn_identifier, update_headers, get_budget_owner, is_furniture_unique, \
    has_special_chars
from utilities.permissions import HasConnection, PermissionPermissions, GroupPermissions, ModelPermissions, \
    IsResourceOwner, CanChangeActivation
from utilities.serializers import ChangePasswordSerializer, AvatarSerializer, MeSerializer, ChangeActivationSerializer
from utilities.signals import project_deleted, furniture_changed
from utilities.signals import user_registered, save_budget, furniture_created, furniture_deleted
from .viewsMixin import OrionInterfaceView, OrionRetrieveMixin, OrionDeleteMixin, OrionUpdateMixin, OrionListMixin, \
    OrionCreateMixin, OrderByRetrieveMixin, OrderByListMixin, OrderByDeleteMixin, OrderByUpdateMixin, \
    OrderByCreateAttrsMixin, OrionCreateAttrsMixin


class UserInterfaceViewSet(viewsets.ModelViewSet):
    """
    The UserInterfaceViewSet class is a base class that is intended to be inherited by other ViewSet classes. Its main
    purpose is to provide a consistent set of validations for the endpoints of the API that are related to user
    interactions. By inheriting from this class, child classes can easily apply a set of predefined validations to
    their endpoints without having to rewrite the same logic multiple times. This can help to improve the overall
    consistency and maintainability of the codebase, as well as making it easier to add new validations in the future.
    Additionally, this class also provides a number of other useful features, such as pagination and filtering, which
    can be easily configured and customized to suit the needs of the child classes. Overall, the UserInterfaceViewSet
    is an essential building block for creating robust and maintainable API endpoints that are tailored to the needs
    of the users.
    """
    register_serializer_class = None
    orion_add_permissions_serializer_class = AddPermissionsSerializer
    orion_add_groups_serializer_class = AddGroupSerializer
    change_password_serializer_class = ChangePasswordSerializer
    avatar_serializer_class = AvatarSerializer
    me_serializer_class = MeSerializer
    change_activation_serializer_class = ChangeActivationSerializer

    def get_current_user(self) -> User:
        return self.request.user

    def get_serializer_class(self):
        if self.action == "create":
            return self.register_serializer_class
        elif self.action == "orion_permissions" or self.action == "orion_permissions_put":
            return self.orion_add_permissions_serializer_class
        elif self.action == "orion_groups" or self.action == "orion_groups_put":
            return self.orion_add_groups_serializer_class
        elif self.action == "change_password":
            return self.change_password_serializer_class
        elif self.action == "avatar":
            return self.avatar_serializer_class
        elif self.action == "me":
            return self.me_serializer_class
        elif self.action == "change_activation":
            return self.change_activation_serializer_class
        elif self.action == "add_to_group":
            return DjangoUserGroupSerializer
        elif self.action == "add_to_group_get":
            return DjangoUserGroupSerializerRead
        return super(UserInterfaceViewSet, self).get_serializer_class()

    def get_instance(self):
        return self.request.user

    @action(detail=False, methods=['get'], description="Get Profile Base info",
            permission_classes=[permissions.IsAdminUser | ModelPermissions])
    def me(self, request):
        # noinspection PyAttributeOutsideInit
        self.get_object = self.get_instance
        user = self.get_object()
        serializer: MeSerializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], description="Get Profile Picture")
    def avatar(self, request: Request, pk: str = None):
        profile = self.get_object()
        data = dict(avatar=profile.user.picture, profile=profile.id)
        representation = self.get_serializer_class()().to_representation(instance=data)
        return Response(data=representation, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def avatar_delete(self, request: Request, pk: str = None):
        profile = self.get_object()
        profile.user.picture.delete()
        profile.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser | PermissionPermissions])
    def orion_permissions(self, request, pk=None):
        profile = self.get_object()
        current_permissions = profile.user.get_orion_permissions()
        instance = dict(permissions=current_permissions, add_permissions=current_permissions)
        serializer: AddPermissionsSerializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, CanChangeActivation])
    def change_activation(self, request, pk=None):
        serializer: ChangeActivationSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        active = serializer.validated_data.get("active", None)
        company = self.get_object()
        company.user.is_active = active
        company.user.save()
        return Response(serializer.data)

    @orion_permissions.mapping.put
    def orion_permissions_put(self, request, pk=None):
        profile = self.get_object()
        current_permissions = profile.user.get_all_orion_permissions()
        serializer: AddPermissionsSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_permissions = serializer.data.get('add_permissions', current_permissions)
        profile.user.user_orion_permissions.set(new_permissions)
        return Response(serializer.data)

    @orion_permissions.mapping.delete
    def orion_permissions_delete(self, request, pk=None):
        profile = self.get_object()
        profile.user.delete_orion_permissions()
        return Response(data=dict(detail="Orion Permissions were deleted!"), status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser | GroupPermissions])
    def orion_groups(self, request, pk=None):
        profile = self.get_object()
        current_groups = profile.user.get_orion_groups()
        instance = dict(groups=current_groups, add_groups=current_groups)
        serializer: AddGroupSerializer = self.get_serializer(instance)
        return Response(serializer.data)

    @orion_groups.mapping.put
    def orion_groups_put(self, request, pk=None):
        profile = self.get_object()
        current_groups = profile.user.get_orion_groups()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_groups = serializer.data.get('add_groups', current_groups)
        profile.user.orion_groups.set(new_groups)
        return Response(serializer.data)

    @orion_groups.mapping.delete
    def orion_groups_delete(self, request, pk=None):
        profile = self.get_object()
        profile.user.delete_orion_groups()
        return Response(data=dict(detail="Orion Groups were deleted!"), status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser | ModelPermissions,
                                                               permissions.IsAdminUser | IsResourceOwner])
    def change_password(self, request, pk=None):
        profile = self.get_object()
        serializer: ChangePasswordSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_password = serializer.data.get("current_password")
        new_password = serializer.data.get("new_password")

        if not profile.user.check_password(current_password):
            return Response({"success": False,
                             "message": ["Wrong password."],
                             "code": status.HTTP_400_BAD_REQUEST,
                             "status": "fail",
                             "ok": False,
                             "cause": "wrong_password"
                             }, status=status.HTTP_400_BAD_REQUEST)
        profile.user.set_password(new_password)
        profile.user.save()

        return Response({
            'status': 'success',
            'code': status.HTTP_200_OK,
            "ok": True,
            'message': 'Password updated successfully',
            'data': []
        }, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        instance = serializer.save()
        user_registered.send(sender=self.__class__, user=instance.user, request=self.request)

    @action(detail=True, methods=['post', ], url_path='add-to-group',
            permission_classes=[permissions.IsAdminUser | permissions.DjangoModelPermissions])
    def add_to_group(self, request, pk=None):
        profile = self.get_object()
        serializer = self.get_serializer(data=request.data, instance=profile.user, )
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User added to group successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @add_to_group.mapping.get
    def add_to_group_get(self, request, pk=None):
        profile = self.get_object()
        serializer = self.get_serializer(instance=profile.user, )
        return Response(serializer.data)


class HomeAPIView(views.APIView):
    """
    This page provides a list of endpoints that the developer can use to create applications.
    """
    views = list()
    namespace_views = list()
    router_views = list()

    def get(self, request):
        apidocs = dict()
        if self.views:
            for view in self.views:
                apidocs[view] = request.build_absolute_uri(reverse(view))
        if self.namespace_views:
            for name, namespace, view in self.namespace_views:
                apidocs[name] = request.build_absolute_uri(reverse(f"{namespace}:{view}"))
        if self.router_views:
            for name, namespace, basename, methods in self.router_views:
                for method in methods:
                    apidocs[f"{name} - {method}"] = \
                        request.build_absolute_uri(reverse(f"{namespace}:{basename}-{method}"))
        return Response({key: apidocs[key] for key in sorted(apidocs)})


class EntityView(OrionInterfaceView, OrionCreateMixin, OrionListMixin):
    permission_classes = [permissions.IsAuthenticated, HasConnection]


class EntityViewDetail(OrionInterfaceView, OrionRetrieveMixin, OrionDeleteMixin, OrionUpdateMixin):
    permission_classes = [permissions.IsAuthenticated, HasConnection]


class OwnerViewEntity(OrionInterfaceView, OrionListMixin):
    permission_classes = [permissions.IsAuthenticated | TokenHasReadWriteScope, HasConnection]
    entity_type = 'Owner'

    @user_has_orion_permission('view_owner')
    def get(self, request: Request):
        return super().get(request)


class OwnerViewEntityDetail(OrionInterfaceView, OrionRetrieveMixin):
    permission_classes = [permissions.IsAuthenticated | TokenHasReadWriteScope, HasConnection]
    entity_type = "Owner"

    @user_has_orion_permission('view_owner')
    def get(self, request: Request, pk):
        return super().get(request, pk)


class OrganizationViewEntity(OrionInterfaceView, OrionListMixin):
    permission_classes = [permissions.IsAuthenticated | TokenHasReadWriteScope, HasConnection]
    entity_type = "Organization"

    @user_has_orion_permission('view_organization')
    def get(self, request: Request):
        return super().get(request)

    def generate_params(self, user):
        params = dict()
        if user.is_admin:
            params = dict(type=self.entity_type)
        elif user.is_worker:
            params = dict(id=generate_urn_identifier(_type=self.entity_type, uid=user.worker.hasOrganization.id))
        return params


class OrganizationViewEntityDetail(OrionInterfaceView, OrionRetrieveMixin):
    permission_classes = [permissions.IsAuthenticated | TokenHasReadWriteScope, HasConnection]
    entity_type = "Organization"

    @user_has_orion_permission('view_organization')
    def get(self, request: Request, pk):
        return super().get(request, pk)


class WorkerViewEntity(OrionInterfaceView, OrionListMixin):
    entity_type = "Worker"

    @user_has_orion_permission('view_worker')
    def get(self, request: Request):
        return super().get(request)

    def generate_params(self, user):
        params = dict()
        if user.is_admin:
            params = dict(type=self.entity_type)
        elif user.is_worker:
            params = dict(q=f'hasOrganization=="urn:ngsi-ld:Organization:{user.worker.hasOrganization.id}"')
        return params


class WorkerViewEntityDetail(OrionInterfaceView, OrionRetrieveMixin):
    entity_type = "Organization"

    @user_has_orion_permission('view_worker')
    def get(self, request: Request, pk):
        return super().get(request, pk)


class ExpeditionViewEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Expedition'

    def generate_params(self, user):
        params = dict()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            params = dict(q=f'orderBy=="{generate_urn_identifier(_type="Owner", uid=user.customer.id)}"',
                          type=self.entity_type)
        params.update(dict(count='true'))
        return params

    @user_has_orion_permission('view_expedition')
    def get(self, request: Request):
        return super().get(request)

    @user_has_orion_permission('add_expedition')
    def post(self, request):
        return super(ExpeditionViewEntity, self).post(request)


class ExpeditionViewEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Expedition'

    @user_has_orion_permission('view_expedition')
    def get(self, request, pk: str):
        return super().get(request, pk)

    @user_has_orion_permission('delete_expedition')
    def delete(self, request, pk: str):
        return super(ExpeditionViewEntityDetail, self).delete(request, pk)


class ExpeditionViewEntityDetailCreateAttrs(OrionInterfaceView, OrderByCreateAttrsMixin):
    entity_type = 'Expedition'

    @user_has_orion_permission('change_expedition')
    def post(self, request, pk: str):
        return super(ExpeditionViewEntityDetailCreateAttrs, self).post(request, pk)


class ProjectViewEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Project'

    @user_has_orion_permission('view_project')
    def get(self, request: Request):
        return super(ProjectViewEntity, self).get(request)

    @user_has_orion_permission('add_project')
    @customer_profile_exists
    def post(self, request):
        return super(ProjectViewEntity, self).post(request)


class ProjectViewEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Project'

    @user_has_orion_permission('view_project')
    def get(self, request, pk: str):
        return super().get(request, pk)

    @user_has_orion_permission('delete_project')
    def delete(self, request, pk):
        project_deleted.send(sender=self.__class__, pk=pk)
        response: Response = super(ProjectViewEntityDetail, self).delete(request, pk)
        return response

    @user_has_orion_permission('change_project')
    def patch(self, request, pk):
        return super().patch(request, pk)


class ConsumableViewEntity(OrionInterfaceView, OrderByListMixin, OrionCreateMixin):
    entity_type = 'Consumable'

    @user_has_orion_permission('view_consumable')
    def get(self, request: Request):
        return super(ConsumableViewEntity, self).get(request)

    @user_has_orion_permission('add_consumable')
    def post(self, request):
        return super(ConsumableViewEntity, self).post(request)


class ConsumableViewEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Consumable'

    @user_has_orion_permission('view_consumable')
    def get(self, request, pk: str):
        return super().get(request, pk)

    @user_has_orion_permission('delete_consumable')
    def delete(self, request, pk):
        return super(ConsumableViewEntityDetail, self).delete(request, pk)

    @user_has_orion_permission('change_consumable')
    def patch(self, request, pk):
        return super().patch(request, pk)


class ConsumableViewEntityDetailCreateAttrs(OrionInterfaceView, OrderByCreateAttrsMixin):
    entity_type = 'Consumable'

    @user_has_orion_permission('change_consumable')
    def post(self, request, pk: str):
        return super().post(request, pk)


class PartViewEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Part'

    @user_has_orion_permission('view_part')
    def get(self, request: Request):
        return super(PartViewEntity, self).get(request)

    @user_has_orion_permission('add_part')
    def post(self, request):
        return super(PartViewEntity, self).post(request)


class PartViewEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Part'

    @user_has_orion_permission('view_part')
    def get(self, request, pk: str):
        return super(PartViewEntityDetail, self).get(request, pk)

    @user_has_orion_permission('delete_part')
    def delete(self, request, pk):
        return super(PartViewEntityDetail, self).delete(request, pk)

    @user_has_orion_permission('change_part')
    def patch(self, request, pk):
        return super(PartViewEntityDetail, self).patch(request, pk)


class PartViewEntityDetailCreateAttrs(OrionInterfaceView, OrderByCreateAttrsMixin):
    entity_type = 'Part'

    @user_has_orion_permission('change_part')
    def post(self, request: Request, pk: str):
        return super(PartViewEntityDetailCreateAttrs, self).post(request, pk)


class LeftOverEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Leftover'

    @user_has_orion_permission('view_leftover')
    def get(self, request: Request):
        return super(LeftOverEntity, self).get(request)

    @user_has_orion_permission('add_leftover')
    def post(self, request):
        return super(LeftOverEntity, self).post(request)


class LeftOverEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Leftover'

    @user_has_orion_permission('view_leftover')
    def get(self, request, pk: str):
        return super(LeftOverEntityDetail, self).get(request, pk)

    @user_has_orion_permission('delete_leftover')
    def delete(self, request, pk):
        return super(LeftOverEntityDetail, self).delete(request, pk)

    @user_has_orion_permission('change_leftover')
    def patch(self, request, pk):
        return super(LeftOverEntityDetail, self).patch(request, pk)


class LeftOverEntityDetailCreateAttrs(OrionInterfaceView, OrderByCreateAttrsMixin):
    entity_type = 'Leftover'

    @user_has_orion_permission('change_leftover')
    def post(self, request: Request, pk: str):
        return super(LeftOverEntityDetailCreateAttrs, self).post(request, pk)


class MachineEntityView(OrionInterfaceView, OrionCreateMixin, OrionListMixin):
    entity_type = 'Machine'

    def generate_params(self, user):
        return dict(type=self.entity_type)

    @user_has_orion_permission('view_machine')
    def get(self, request: Request):
        return super(MachineEntityView, self).get(request)

    @user_has_orion_permission('add_machine')
    def post(self, request):
        return super(MachineEntityView, self).post(request)


class MachineEntityViewDetail(OrionInterfaceView, OrionRetrieveMixin, OrionDeleteMixin, OrionUpdateMixin):
    entity_type = 'Machine'

    @user_has_orion_permission('view_machine')
    def get(self, request, pk: str):
        return super(MachineEntityViewDetail, self).get(request, pk)

    @user_has_orion_permission('delete_machine')
    def delete(self, request, pk):
        return super(MachineEntityViewDetail, self).delete(request, pk)

    @user_has_orion_permission('change_machine')
    def patch(self, request, pk):
        return super(MachineEntityViewDetail, self).patch(request, pk)


class MachineEntityViewDetailCreateAttrs(OrionInterfaceView, OrionCreateAttrsMixin):
    entity_type = 'Machine'

    @user_has_orion_permission('change_machine')
    def post(self, request, pk: str):
        return super(MachineEntityViewDetailCreateAttrs, self).post(request, pk)


class FurnitureEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Furniture'

    @user_has_orion_permission('view_furniture')
    def get(self, request: Request):
        return super(FurnitureEntity, self).get(request)

    @staticmethod
    def validate_data(data: dict) -> dict:
        furniture_type = data.get('furnitureType')
        group = data.get('group')
        name = data.get("name")
        pk = data.get("name")
        sub_group = data.get('subGroup')
        budget_id = data.get("hasBudget")
        if pk is None:
            raise ValidationError("The presence of the attribute 'id' is mandatory and cannot be omitted.")
        if budget_id is None:
            raise ValidationError("The presence of the attribute 'hasBudget' is mandatory and cannot be omitted.")
        if isinstance(budget_id, dict):
            budget_id = budget_id.get('object')

        if name is None:
            raise ValidationError("The presence of the attribute 'name' is mandatory and cannot be omitted.")

        if furniture_type is None:
            raise ValidationError("The presence of the attribute 'furnitureType' is mandatory and cannot be omitted.")
        if furniture_type.get('value') == FurnitureType.FURNITURE.value:
            if sub_group is None or group is None:
                raise ValidationError("If the value of the 'furnitureType' attribute is set to 'furniture', then the"
                                      " presence of the 'group' and 'subGroup' attributes is mandatory and cannot be "
                                      "omitted.")
        elif furniture_type.get("value") == FurnitureType.SUBGROUP.value:
            if group is None:
                raise ValidationError("If the value of the 'furnitureType' attribute is set to 'subGroup', then the "
                                      "presence of the 'group'  attribute is mandatory and cannot be omitted.")

        customer = get_budget_owner(budget_id=budget_id)
        if customer is None:
            raise ValidationError("The system was unable to locate a customer associated with the budget specified")
        name = name.get("value")
        if has_special_chars(name=name):
            raise ValidationError("The attribute 'name' must only contain ASCII characters.")
        furniture_type = furniture_type.get("value")
        if not is_furniture_unique(name=name, budget_id=budget_id, furniture_type=furniture_type):
            raise ValidationError(f"A furniture with the name '{name}', the ID '{budget_id}', and the furniture type"
                                  f" '{furniture_type}' already exists.")
        return data

    @user_has_orion_permission('add_furniture')
    def post(self, request):
        datas = request.data
        pks = list()
        if isinstance(datas, list):
            for data in datas:
                self.validate_data(data)
                pks.append(data.get('id'))
        else:
            self.validate_data(datas)
            pks.append(datas.get("id"))
        response: Response = super(FurnitureEntity, self).post(request)
        if response.status_code == 201:
            furniture_created.send(sender=self.__class__, pks=pks)
        elif response.status_code == 207:
            pks = response.data.get('success')
            if pks:
                furniture_created.send(sender=self.__class__, pks=pks)
        return response


class FurnitureEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Furniture'

    @user_has_orion_permission('view_furniture')
    def get(self, request, pk: str):
        return super(FurnitureEntityDetail, self).get(request, pk)

    @user_has_orion_permission('delete_furniture')
    def delete(self, request, pk):
        data = self.get_object(pk)
        if not data.status_code == status.HTTP_200_OK:
            return Response(dict(message="No entity found!", ok=False, status=status.HTTP_404_NOT_FOUND),
                            status=status.HTTP_404_NOT_FOUND, headers=update_headers(data.headers))
        furniture_deleted.send(sender=self.__class__, pk=pk)
        response: Response = super(FurnitureEntityDetail, self).delete(request, pk)

        return response

    @user_has_orion_permission('change_furniture')
    def patch(self, request, pk=None):
        old_name = self.get_object(pk=pk).json().get('name').get('value')
        response = super(FurnitureEntityDetail, self).patch(request, pk)
        if response.status_code == 201:
            furniture_changed.send(sender=self.__class__, pk=pk, old_name=old_name)
        return response


class FurnitureEntityDetailCreateAttrs(OrionInterfaceView, OrderByCreateAttrsMixin):
    entity_type = 'Furniture'

    @user_has_orion_permission('change_furniture')
    def post(self, request, pk: str):
        return super(FurnitureEntityDetailCreateAttrs, self).post(request, pk)


class OrderByBudgetEntityView(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Budget'

    @user_has_orion_permission('view_budget')
    def get(self, request: Request):
        return super(OrderByBudgetEntityView, self).get(request)

    @user_has_orion_permission('add_budget')
    @customer_profile_exists
    def post(self, request):
        response: Response = super(OrderByBudgetEntityView, self).post(request)
        if response.status_code == 201:
            pk = response.data.get('id')
            save_budget.send(sender=self.__class__, budget_id=pk)
        return response


class OrderByBudgetEntityViewDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Budget'

    @user_has_orion_permission('view_budget')
    def get(self, request, pk: str):
        return super(OrderByBudgetEntityViewDetail, self).get(request, pk)

    @user_has_orion_permission('delete_budget')
    def delete(self, request, pk):
        return super(OrderByBudgetEntityViewDetail, self).delete(request, pk)

    @user_has_orion_permission('change_budget')
    def patch(self, request, pk):
        return super(OrderByBudgetEntityViewDetail, self).patch(request, pk)


class OrderByBudgetEntityViewDetailCreateAttrs(OrionInterfaceView, OrderByCreateAttrsMixin, OrderByDeleteMixin):
    entity_type = 'Budget'

    @user_has_orion_permission('change_budget')
    def post(self, request: Request, pk: str):
        return super(OrderByBudgetEntityViewDetailCreateAttrs, self).post(request, pk)


class OrderByAssemblyEntityView(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Assembly'

    @user_has_orion_permission('view_assembly')
    def get(self, request: Request):
        return super(OrderByAssemblyEntityView, self).get(request)

    @user_has_orion_permission('add_assembly')
    def post(self, request):
        return super(OrderByAssemblyEntityView, self).post(request)


class OrderByAssemblyEntityViewDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Assembly'

    @user_has_orion_permission('view_assembly')
    def get(self, request, pk: str):
        return super(OrderByAssemblyEntityViewDetail, self).get(request, pk)

    @user_has_orion_permission('delete_assembly')
    def delete(self, request, pk):
        return super(OrderByAssemblyEntityViewDetail, self).delete(request, pk)

    @user_has_orion_permission('change_assembly')
    def patch(self, request, pk):
        return super(OrderByAssemblyEntityViewDetail, self).patch(request, pk)


class OrderByAssemblyEntityViewDetailCreateAttrs(OrionInterfaceView, OrderByCreateAttrsMixin):
    entity_type = 'Assembly'

    @user_has_orion_permission('change_assembly')
    def post(self, request, pk):
        return super(OrderByAssemblyEntityViewDetailCreateAttrs, self).post(request, pk)


class WorkerTaskEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'WorkerTask'

    @user_has_orion_permission('view_workerTask')
    def get(self, request: Request):
        return super(WorkerTaskEntity, self).get(request)

    @user_has_orion_permission('add_workerTask')
    def post(self, request):
        return super(WorkerTaskEntity, self).post(request)


class WorkerTaskEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'WorkerTask'

    @user_has_orion_permission('view_workerTask')
    def get(self, request, pk: str):
        return super(WorkerTaskEntityDetail, self).get(request, pk)

    @user_has_orion_permission('delete_workerTask')
    def delete(self, request, pk):
        return super(WorkerTaskEntityDetail, self).delete(request, pk)

    @user_has_orion_permission('change_workerTask')
    def patch(self, request, pk):
        return super(WorkerTaskEntityDetail, self).patch(request, pk)


class WorkerTaskEntityDetailCreateAttrs(OrionInterfaceView, OrionCreateAttrsMixin):
    entity_type = 'WorkerTask'

    @user_has_orion_permission('change_workerTask')
    def post(self, request, pk: str):
        return super(WorkerTaskEntityDetailCreateAttrs, self).post(request, pk)


class MachineTaskEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'MachineTask'

    @user_has_orion_permission('view_machineTask')
    def get(self, request: Request):
        return super(MachineTaskEntity, self).get(request)

    @user_has_orion_permission('add_machineTask')
    def post(self, request):
        return super(MachineTaskEntity, self).post(request)


class MachineTaskEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'MachineTask'

    @user_has_orion_permission('view_machineTask')
    def get(self, request, pk: str):
        return super(MachineTaskEntityDetail, self).get(request, pk)

    @user_has_orion_permission('delete_machineTask')
    def delete(self, request, pk):
        return super(MachineTaskEntityDetail, self).delete(request, pk)

    @user_has_orion_permission('change_machineTask')
    def patch(self, request, pk):
        return super(MachineTaskEntityDetail, self).patch(request, pk)


class ModuleEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Module'

    @user_has_orion_permission('view_module')
    def get(self, request: Request):
        return super(ModuleEntity, self).get(request)

    @user_has_orion_permission('add_module')
    def post(self, request):
        return super(ModuleEntity, self).post(request)


class ModuleEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Module'

    @user_has_orion_permission('view_module')
    def get(self, request, pk: str):
        return super(ModuleEntityDetail, self).get(request, pk)

    @user_has_orion_permission('delete_module')
    def delete(self, request, pk):
        return super(ModuleEntityDetail, self).delete(request, pk)

    @user_has_orion_permission('change_module')
    def patch(self, request, pk):
        return super(ModuleEntityDetail, self).patch(request, pk)


class ModuleEntityDetailCreateAttrs(OrionInterfaceView, OrionCreateAttrsMixin):
    entity_type = 'Module'

    @user_has_orion_permission('change_module')
    def post(self, request, pk):
        return super(ModuleEntityDetailCreateAttrs, self).post(request, pk)


class GroupEntity(OrderByListMixin, OrionInterfaceView, OrionCreateMixin):
    entity_type = 'Group'

    @user_has_orion_permission('view_group')
    def get(self, request: Request):
        return super(GroupEntity, self).get(request)

    @user_has_orion_permission('add_group')
    def post(self, request):
        return super(GroupEntity, self).post(request)


class GroupEntityDetail(OrionInterfaceView, OrderByRetrieveMixin, OrderByDeleteMixin, OrderByUpdateMixin):
    entity_type = 'Group'

    @user_has_orion_permission('view_group')
    def get(self, request, pk: str):
        return super(GroupEntityDetail, self).get(request, pk)

    @user_has_orion_permission('delete_group')
    def delete(self, request, pk):
        return super(GroupEntityDetail, self).delete(request, pk)

    @user_has_orion_permission('change_group')
    def patch(self, request, pk):
        return super(GroupEntityDetail, self).patch(request, pk)
