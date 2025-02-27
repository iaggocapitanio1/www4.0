from django.db.models.query import QuerySet
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from utilities.functions import get_projects_based_on_owner, generate_urn_identifier, get_budgets, get_furniture, \
    convert_list_into_string
from utilities.signals import budget_changed, budget_deleted
from utilities.views import (HomeAPIView, OwnerViewEntity, OwnerViewEntityDetail, OrganizationViewEntity,
                             OrganizationViewEntityDetail, WorkerViewEntity, WorkerViewEntityDetail,
                             ExpeditionViewEntity, ExpeditionViewEntityDetail, ProjectViewEntity,
                             ProjectViewEntityDetail, ConsumableViewEntity, ConsumableViewEntityDetail,
                             MachineEntityViewDetail, MachineEntityView, PartViewEntity, PartViewEntityDetail,
                             OrderByAssemblyEntityViewDetail, OrderByAssemblyEntityView, OrderByBudgetEntityView,
                             OrderByBudgetEntityViewDetail, LeftOverEntityDetail, LeftOverEntity, FurnitureEntity,
                             FurnitureEntityDetail, WorkerTaskEntityDetail, WorkerTaskEntity, ModuleEntity,
                             ModuleEntityDetail, MachineTaskEntity, GroupEntity, GroupEntityDetail,
                             MachineTaskEntityDetail, OrderByBudgetEntityViewDetailCreateAttrs,
                             ExpeditionViewEntityDetailCreateAttrs, OrderByAssemblyEntityViewDetailCreateAttrs,
                             ConsumableViewEntityDetailCreateAttrs, PartViewEntityDetailCreateAttrs,
                             LeftOverEntityDetailCreateAttrs, MachineEntityViewDetailCreateAttrs,
                             FurnitureEntityDetailCreateAttrs, WorkerTaskEntityDetailCreateAttrs,
                             ModuleEntityDetailCreateAttrs,
                             )
from .serializers import CheckSerializer


class AssemblyView(OrderByAssemblyEntityView):
    entity_type = 'Assembly'

    def generate_params(self, user):
        params = dict()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
            projects: list = get_projects_based_on_owner(owner_id=owner_id)
            params = dict(q=f'belongsTo=={convert_list_into_string(projects)}',
                          type=self.entity_type)
        params.update(dict(count='true'))
        return params


class AssemblyViewDetail(OrderByAssemblyEntityViewDetail):
    entity_type = 'Assembly'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class AssemblyViewDetailCreateAttrs(OrderByAssemblyEntityViewDetailCreateAttrs):
    entity_type = 'Assembly'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class BudgetView(OrderByBudgetEntityView):
    entity_type = 'Budget'


class BudgetViewDetail(OrderByBudgetEntityViewDetail):
    entity_type = 'Budget'

    def delete(self, request, pk):
        budget_deleted.send(sender=self.__class__, pk=pk)
        response: Response = super().delete(request, pk)
        return response

    def patch(self, request, pk):
        response = self.get_object(pk)
        if response.status_code == 200:
            budget_changed.send(sender=self.__class__, data=request.data, budget=response.json())
        return super().patch(request, pk)


class BudgetViewDetailCreateAttrs(OrderByBudgetEntityViewDetailCreateAttrs):
    entity_type = 'Budget'

    def post(self, request, pk):
        response = self.get_object(pk)
        if response.status_code == 200:
            budget_changed.send(sender=self.__class__, data=request.data, budget=response.json())
        return super().post(request, pk)


class ConsumableView(ConsumableViewEntity):
    entity_type = 'Consumable'

    def generate_params(self, user):
        params = dict()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
            projects: list = get_projects_based_on_owner(owner_id=owner_id)
            params = dict(q=f'belongsTo=={convert_list_into_string(projects)}',
                          type=self.entity_type)
        params.update(dict(count='true'))
        return params


class ConsumableViewDetail(ConsumableViewEntityDetail):
    entity_type = 'Consumable'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user is None:
            return True
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class ConsumableViewDetailCreateAttrs(ConsumableViewEntityDetailCreateAttrs):
    entity_type = 'Consumable'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class ExpeditionView(ExpeditionViewEntity):
    entity_type = 'Expedition'

    def generate_params(self, user):
        params = dict()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
            projects: list = get_projects_based_on_owner(owner_id=owner_id)
            params = dict(q=f'belongsTo=={convert_list_into_string(ids=projects)}',
                          type=self.entity_type)
        params.update(dict(count='true'))
        return params


class ExpeditionViewDetail(ExpeditionViewEntityDetail):
    entity_type = 'Expedition'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class ExpeditionViewDetailCreateAttrs(ExpeditionViewEntityDetailCreateAttrs):
    entity_type = 'Expedition'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class MachineView(MachineEntityView):
    entity_type = 'Machine'


class MachineViewDetail(MachineEntityViewDetail):
    entity_type = 'Machine'


class MachineViewDetailCreateAttrs(MachineEntityViewDetailCreateAttrs):
    entity_type = 'Machine'


class OrganizationView(OrganizationViewEntity):
    entity_type = 'Organization'


class OrganizationViewDetail(OrganizationViewEntityDetail):
    entity_type = 'Organization'


class OwnerView(OwnerViewEntity):
    entity_type = 'Owner'
    use_owner = False
    allow_id = False


class OwnerViewDetail(OwnerViewEntityDetail):
    entity_type = 'Owner'


class PartView(PartViewEntity):
    entity_type = 'Part'

    def generate_params(self, user):
        params = dict()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
            projects: list = get_projects_based_on_owner(owner_id=owner_id)
            params = dict(q=f'belongsTo=={convert_list_into_string(projects)}',
                          type=self.entity_type)
        params.update(dict(count='true'))
        return params


class PartViewDetail(PartViewEntityDetail):
    entity_type = 'Part'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user is None:
            return True
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class PartViewDetailCreateAttrs(PartViewEntityDetailCreateAttrs):
    entity_type = 'Part'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class Leftover(LeftOverEntity):
    entity_type = 'Leftover'

    @staticmethod
    def get_current_id(user):
        from utilities.functions import generate_urn_identifier
        if user.is_customer:
            current_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
        elif user.is_worker:
            current_id = generate_urn_identifier(_type="Organization", uid=user.worker.hasOrganization.id)
        elif user.is_superuser:
            current_id = generate_urn_identifier(_type="Admin", uid=user.id)
        else:
            current_id = generate_urn_identifier(_type="Organization", uid=user.organization.id)
        return current_id

    # def generate_params(self, user):
    #     params = dict()
    #     current_id = self.get_current_id(user)
    #     params.update(dict(count='true', q=f'orderBy=="{self.get_organization(current_id)}"', type=self.entity_type))
    #     return params

    @staticmethod
    def get_organization(current_owner_id: str) -> str:
        from utilities.functions import generate_urn_identifier
        from users.models import User
        users: QuerySet = User.objects.filter(role=0)
        staffs: QuerySet = User.objects.filter(is_staff=True)
        if users.exists():
            return generate_urn_identifier(_type='Organization', uid=users.first().id)
        elif staffs.exists():
            return generate_urn_identifier(_type='Admin', uid=users.first().id)
        return current_owner_id

    def check_data(self, data: dict):
        _type = data.get("type", None)
        order_by = self.get_organization(data.get('orderBy', ''))
        if _type is not None:
            data.update(dict(type=self.entity_type))
        data.update(dict(orderBy=order_by))
        return data


class LeftoverDetail(LeftOverEntityDetail):
    entity_type = 'Leftover'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class LeftoverDetailCreateAttrs(LeftOverEntityDetailCreateAttrs):
    entity_type = 'Leftover'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('belongsTo').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('belongsTo').get('object') in get_projects_based_on_owner(owner_id=owner_id)
            return False
        return True


class ProjectView(ProjectViewEntity):
    entity_type = 'Project'


class ProjectViewDetail(ProjectViewEntityDetail):
    entity_type = 'Project'


class WorkerView(WorkerViewEntity):
    entity_type = 'Worker'


class WorkerViewDetail(WorkerViewEntityDetail):
    entity_type = 'Worker'


class FurnitureView(FurnitureEntity):
    entity_type = 'Furniture'

    def generate_params(self, user):
        params = dict()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
            budgets: list = get_budgets(owner_id=owner_id)
            params = dict(q=f'hasBudget=={convert_list_into_string(budgets)}',
                          type=self.entity_type)
        params.update(dict(count='true'))
        return params


class FurnitureViewDetail(FurnitureEntityDetail):
    entity_type = 'Furniture'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('hasBudget').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('hasBudget').get('object') in get_budgets(owner_id=owner_id)
            return False
        return True


class FurnitureViewDetailCreateAttrs(FurnitureEntityDetailCreateAttrs):
    entity_type = 'Furniture'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user.is_customer:
            if payload.get('hasBudget').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                return payload.get('hasBudget').get('object') in get_budgets(owner_id=owner_id)
            return False
        return True


class WorkerTaskView(WorkerTaskEntity):
    entity_type = 'WorkerTask'


class WorkerTaskDetail(WorkerTaskEntityDetail):
    entity_type = 'WorkerTask'


class WorkerTaskDetailCreateAttrs(WorkerTaskEntityDetailCreateAttrs):
    entity_type = 'WorkerTask'


class MachineTaskView(MachineTaskEntity):
    entity_type = 'MachineTask'


class MachineTaskDetail(MachineTaskEntityDetail):
    entity_type = 'MachineTask'


class ModuleView(ModuleEntity):
    entity_type = 'Module'

    def generate_params(self, user):
        params = dict()
        tmp = list()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
            budgets: list = get_budgets(owner_id=owner_id)
            for budget in budgets:
                tmp.extend(get_furniture(budget_id=budget))
            params = dict(q=f'belongsToFurniture=={convert_list_into_string(tmp)}',
                          type=self.entity_type)
        params.update(dict(count='true'))
        return params


class ModuleViewDetail(ModuleEntityDetail):
    entity_type = 'Module'


class GroupView(GroupEntity):
    entity_type = 'Group'

    def generate_params(self, user):
        params = dict()
        tmp = list()
        if user is None:
            return dict(type=self.entity_type)
        if user.is_admin or user.is_worker:
            params = dict(type=self.entity_type)
        elif user.is_customer:
            owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
            tmp.extend(get_projects_based_on_owner(owner_id=owner_id))
            params = dict(q=f'belongsTo=={convert_list_into_string(tmp)}', type=self.entity_type)
        params.update(dict(count='true'))
        return params


class ModuleViewDetailCreateAttrs(ModuleEntityDetailCreateAttrs):
    entity_type = 'Module'

    @staticmethod
    def verify_orderBy(payload, user) -> bool:
        if user is None:
            return  True
        if user.is_customer:
            if payload.get('belongsToFurniture').get('object'):
                owner_id = generate_urn_identifier(_type="Owner", uid=user.customer.id)
                budgets = get_budgets(owner_id=owner_id)
                for budget in budgets:
                    if payload.get('belongsToFurniture').get('object') in get_furniture(budget_id=budget):
                        return True
            return False
        return True


class GroupViewDetail(GroupEntityDetail):
    entity_type = 'Group'


class CheckUnique(GenericAPIView):
    serializer_class = CheckSerializer

    def post(self, request) -> Response:
        from users.models import User
        from rest_framework import status
        serialized: CheckSerializer = self.get_serializer(data=request.data)
        serialized.is_valid(raise_exception=True)
        data = serialized.validated_data
        field = data.get('field')
        value: str = data.get('value')
        value = value.strip().lower()
        user_set: QuerySet = User.objects.filter(**{field: value})
        result = dict(is_unique=not user_set.exists())
        return Response(data=result, status=status.HTTP_200_OK)


class HomeView(HomeAPIView):
    """
    Developer: Iaggo Capitanio - email: iaggo.capitanio@gmail.com

    Project: Wood Work Project 4.0

    Home API View

    This page provides a list of endpoints that the developer can use to create applications.
    """
    views = ['assembly', 'budget', 'check', 'consumable', 'expedition', 'furniture', 'group', 'leftover', 'machine',
             'module', 'organization', 'owner', 'part', 'project', 'worker', 'worker-task']

    namespace_views = [
        ("Register New User as Customer", "users", "register"),
        ("Reset Password", "users", "reset-password"),
        ("Get Customer ID", "users", "get-customer"),
        # ("Check Reset Password", "users", "reset-password-check"),

        #                    ("Social OAuth2 Convert Token", "drf", "convert_token"),
        ("Email Service", "email", "service"),
        ("Reset Password", "users", "reset-password"),
        ("Resend Activation Link", "users", "reactivate"),
        ("Get Gran Type Password Token", "drf", "token"),
        ("Invalidate Token", "drf", "revoke_token"),
        ("Invalidate Sessions", "drf", "invalidate_sessions"),
    ]
    router_views = [
        ('Customer', 'users', 'customer', ['list']),
        ('Organization', 'users', 'organization', ['list']),
        ('Worker', 'users', 'worker', ['list']),
        ('Address', 'users', 'address', ['list']),
        ("Permissions", "permissions", "permission", ['list']),
        ("Django Groups", "permissions", "group-management", ["list"]),
        # ("Cut List", "storages", "cut-list", ["list"]),
        ("Folders", "storages", "folder", ["list"]),
        ("Files", "storages", "file", ["list"]),
        ("Leftover", "storages", "leftover", ['list']),
        ("Groups", "permissions", "group", ['list']),
        ("Messages", "chat", "message", ['list']),
        ('Tags', 'tags', 'tag', ['list']),
        ('Tag Result', 'tags', 'tag-result', ['list']),

    ]
