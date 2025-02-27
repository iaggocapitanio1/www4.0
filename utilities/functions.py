import base64
import hashlib
import hmac
import json
import logging
import os
import shutil
import re
import string
from importlib import import_module
from pathlib import Path
from typing import Union, Optional, List, Any

import requests
from django.conf import settings
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.request import Request

from utilities.client import oauth
from utilities.constants import FurnitureType

logger = logging.Logger(__name__)


def generate_urn_identifier(_type: str, uid: str) -> str:
    """
    The purpose of this function is to create an identifier following the Fiware standards for the NGSI-LD API.
    """
    return f"urn:ngsi-ld:{_type}:{uid}"


def get_postcode_validator(country_code):
    """
    This function aims to fetch a zip code validator from the localflavours library. Basically, based on the chosen
    country code, this function will look for the forms module inside the package: localflavours.<country code>
    and if it exists, the zip code will be validated.
    """
    package = 'localflavor.%s' % country_code.lower()
    try:
        module = import_module('.forms', package=package)

    except ModuleNotFoundError:
        return lambda x: x

    except ImportError:
        # No forms module for this country
        return lambda x: x

    field_name_variants = ['%sPostcodeField',
                           '%sPostCodeField',
                           '%sPostalCodeField',
                           '%sZipCodeField', ]

    for variant in field_name_variants:
        field_name = variant % country_code.upper()
        if hasattr(module, field_name):
            return getattr(module, field_name)().clean
    return lambda x: x


def user_is_related(user) -> bool:
    return any([hasattr(user, name) for name in [f.name for f in user._meta.get_fields() if f.one_to_one]])


def serialize_address(address_instance) -> dict:
    """
        This function aims to get an address instance and turn it to a python dictionary.
        :type address_instance: Address
    """
    discard = ['id', 'created', 'modified']
    fields = [field.name for field in address_instance.__class__._meta.get_fields() if not field.is_relation
              and (field.name not in discard)]
    address = dict()
    if address_instance:
        for field in fields:
            address[field] = getattr(address_instance, field).__str__()
    return address


def random_string(length: int) -> str:
    import string
    import random
    return ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase, k=length))


def generate_random_string(random_str_length: int, field: str, model):
    generated: str = random_string(length=random_str_length)
    customer_set = model.objects.filter(**{field: generated})
    if not customer_set.exists():
        return generated
    return generate_random_string(random_str_length, field, model)


def update_headers(response_headers: Union[dict, requests.models.CaseInsensitiveDict]) -> dict:
    headers: dict = response_headers.copy()
    if headers.get('Content-Length'):
        headers.pop('Content-Length')
    if headers.get('Connection'):
        headers.pop('Connection')
    if headers.get('Keep-Alive'):
        headers.pop('Keep-Alive')
    return headers


def get_query_params(request: Request) -> dict:
    kwargs: dict = request.query_params.copy()
    if kwargs.get('type'):
        kwargs.pop('type')
    return kwargs


def flat_list(original_list: list) -> list:
    from itertools import chain
    return list(chain.from_iterable(original_list))


def generate_perms(resource: str, methods: list = None):
    if not isinstance(methods, list) or methods is None:
        methods = ['add', 'change', 'delete', 'view']
    return [f"{method}_{resource}" for method in methods]


def upload_avatar_to(instance, filename):
    import os
    _, ext = os.path.splitext(filename)
    return f'internal/{instance.email}/profile/avatar{ext}'


def normalize_folder_name(name: str) -> str:
    return name.strip().lower().replace(':', '_').replace(' ', '_')


def upload_files_to(instance, filename):
    path = Path(instance.get_file_path())
    return path


def upload_leftover_to(instance, filename):
    import os
    if instance.id is None:
        return f"internal/leftovers/images/{instance.batch}/{filename}"
    _, ext = os.path.splitext(filename)
    return f'internal/leftovers/images/{instance.batch}/{instance.id}{ext}'


def upload_easm_to(instance, filename) -> str:
    return f"internal/3D/{instance.owner.id.__str__()}/{normalize_folder_name(instance.project)}/{filename}"


def upload_cut_list_to(instance, filename) -> str:
    return f"internal/lists/{instance.owner.id.__str__()}/{normalize_folder_name(instance.project)}/{filename}"


def upload_alpha_to(instance, filename) -> str:
    return f"internal/alpha/{instance.owner.id.__str__()}/{normalize_folder_name(instance.project)}/{filename}"


def upload_pdf_to(instance, filename):
    import os
    _, ext = os.path.splitext(filename)
    return f'internal/{instance.project_owner.id.__str__()}/tags/' \
           f'{normalize_folder_name(instance.project.__str__())}/{filename}'


def upload_result_pdf_to(instance, filename):
    import os
    _, ext = os.path.splitext(filename)
    return f'internal/{instance.tag.project_owner.id.__str__()}/tags/' \
           f'{normalize_folder_name(instance.tag.project.__str__())}/{filename}'


def generate_password(username):
    if "@" in username:
        username = username.split("@")[0]
    target = username
    target_base64 = base64.b64encode(target.encode('utf-8')).decode('utf-8')
    encoded = target_base64.rstrip('=').__str__()
    if len(encoded) < 16:
        return "changeMe_" + encoded
    return "changeMe_" + encoded[0:16]


def batch_delete(entities_map: dict, ):
    url = settings.ORION_HOST + "/ngsi-ld/v1/entityOperations/delete"
    entities = list()
    for item in entities_map.items():
        for entity in item[1]:
            entities.append(entity)
    if entities:
        return requests.post(url=url, data=json.dumps(entities), headers=settings.ORION_HEADERS, auth=oauth)


def query(entity_type: str, params=None) -> requests.Response:
    if params is None:
        params = dict()
    return requests.request("GET", f"{settings.ORION_ENTITIES}?type={entity_type}&options=keyValues",
                            headers=settings.ORION_HEADERS, params=params, auth=oauth)


def get_entity(pk: str, params=None) -> requests.Response:
    url: str = settings.ORION_ENTITIES
    if not url.endswith('/'):
        url += '/'
    url += f'{pk}/?options=keyValues'
    if params is None:
        params = dict()
    return requests.get(url, headers=settings.ORION_HEADERS, params=params, auth=oauth)


def get_entities(entity_type: str, params: dict) -> list:
    entities = list(query(entity_type=entity_type, params=params).json())
    return [entity.get('id', None) for entity in entities]


def get_budgets(owner_id: str) -> list:
    params = dict(q=f'orderBy==\"{owner_id}\"')
    entity_type = 'Budget'
    return get_entities(entity_type, params)


def get_projects(budget_id: str) -> list:
    params = dict(q=f'hasBudget==\"{budget_id}\"')
    entity_type = "Project"
    return get_entities(entity_type, params)


def get_projects_based_on_owner(owner_id: str) -> list:
    params = dict(q=f'orderBy==\"{owner_id}\"')
    entity_type = "Project"
    return get_entities(entity_type, params)


def get_assemblies(project_id: str) -> list:
    params = dict(q=f'belongsTo==\"{project_id}\"')
    entity_type = "Assembly"
    return get_entities(entity_type, params)


def get_furniture(budget_id: str) -> list:
    params = dict(q=f'hasBudget==\"{budget_id}\"')
    entity_type = "Furniture"
    return get_entities(entity_type, params)


def get_modules(furniture_id: str) -> list:
    params = dict(q=f'belongsToFurniture==\"{furniture_id}\"')
    entity_type = "Module"
    return get_entities(entity_type, params)


def get_groups(project_id: str) -> list:
    params = dict(q=f'belongsTo==\"{project_id}\"')
    entity_type = "Group"
    return get_entities(entity_type, params)


def get_consumables(project_id) -> list:
    params = dict(q=f'belongsTo==\"{project_id}\"')
    entity_type = "Consumable"
    return get_entities(entity_type, params)


def get_expeditions(project_id: str) -> list:
    params = dict(q=f'belongsTo==\"{project_id}\"')
    entity_type = "Expedition"
    return get_entities(entity_type, params)


def get_parts(project_id: str) -> list:
    params = dict(q=f'belongsTo==\"{project_id}\"')
    entity_type = "Part"
    return get_entities(entity_type, params)


def get_workerTasks(part_id: str) -> list:
    params = dict(q=f'executedIn==\"{part_id}\"')
    entity_type = "WorkerTask"
    return get_entities(entity_type, params)


def get_machineTasks(part_id: str) -> list:
    params = dict(q=f'performedOn==\"{part_id}\"')
    entity_type = "MachineTask"
    return get_entities(entity_type, params)


def is_furniture_unique(name, budget_id, furniture_type) -> bool:
    params = dict(q=f'name==\"{name}\";hasBudget==\"{budget_id}\";furnitureType==\"{furniture_type}\"')
    entity_type = "Furniture"
    return len(get_entities(entity_type, params)) == 0


def map_parts_entities(part_id: str) -> dict:
    results = dict()
    work_task_tmp = list()
    machine_task_tmp = list()
    work_task_tmp.extend(get_workerTasks(part_id=part_id))
    machine_task_tmp.extend(get_machineTasks(part_id=part_id))
    results['WorkTask'] = work_task_tmp
    results['MachineTask'] = machine_task_tmp
    return results


def map_project_entities(project_id: str) -> dict:
    results = dict()
    consumables_tmp = list()
    expeditions_tmp = list()
    assemblies_tmp = list()
    group_tmp = list()
    parts_tmp = list()
    work_task_tmp = list()
    machine_task_tmp = list()
    consumables_tmp.extend(get_consumables(project_id=project_id))
    expeditions_tmp.extend(get_expeditions(project_id=project_id))
    group_tmp.extend(get_groups(project_id=project_id))
    parts = get_parts(project_id=project_id)
    parts_tmp.extend(parts)
    for part in parts:
        work_task_tmp.extend(get_workerTasks(part_id=part))
        machine_task_tmp.extend(get_machineTasks(part_id=part))
    assemblies = get_assemblies(project_id=project_id)
    assemblies_tmp.extend(assemblies)
    results['Consumable'] = consumables_tmp
    results['Expedition'] = expeditions_tmp
    results['Assembly'] = assemblies_tmp
    results['Group'] = group_tmp
    results['Part'] = parts_tmp
    results['WorkTask'] = work_task_tmp
    results['MachineTask'] = machine_task_tmp
    return results


def map_budget_entities(budget_id: str) -> dict:
    results = dict()
    projects_tmp = list()
    consumables_tmp = list()
    expeditions_tmp = list()
    assemblies_tmp = list()
    furniture_tmp = list()
    modules_tmp = list()
    group_tmp = list()
    parts_tmp = list()
    work_task_tmp = list()
    machine_task_tmp = list()
    projects = get_projects(budget_id=budget_id)
    projects_tmp.extend(projects)
    furniture = get_furniture(budget_id=budget_id)
    furniture_tmp.extend(furniture)
    for furn in furniture:
        modules = get_modules(furniture_id=furn)
        modules_tmp.extend(modules)
    for project in projects:
        consumables_tmp.extend(get_consumables(project_id=project))
        expeditions_tmp.extend(get_expeditions(project_id=project))
        group_tmp.extend(get_groups(project_id=project))
        parts = get_parts(project_id=project)
        parts_tmp.extend(parts)
        for part in parts:
            work_task_tmp.extend(get_workerTasks(part_id=part))
            machine_task_tmp.extend(get_machineTasks(part_id=part))
        assemblies = get_assemblies(project_id=project)
        assemblies_tmp.extend(assemblies)
    results['Project'] = projects_tmp
    results['Consumable'] = consumables_tmp
    results['Expedition'] = expeditions_tmp
    results['Assembly'] = assemblies_tmp
    results['Furniture'] = furniture_tmp
    results['Module'] = modules_tmp
    results['Group'] = group_tmp
    results['Part'] = parts_tmp
    results['WorkTask'] = work_task_tmp
    results['MachineTask'] = machine_task_tmp
    return results


def map_owner_entities(owner_id: str) -> dict:
    results = dict()
    projects_tmp = list()
    consumables_tmp = list()
    expeditions_tmp = list()
    assemblies_tmp = list()
    furniture_tmp = list()
    modules_tmp = list()
    group_tmp = list()
    parts_tmp = list()
    work_task_tmp = list()
    machine_task_tmp = list()
    for budget in get_budgets(owner_id):
        projects = get_projects(budget_id=budget)
        projects_tmp.extend(projects)
        furniture = get_furniture(budget_id=budget)
        furniture_tmp.extend(furniture)
        for furn in furniture:
            modules = get_modules(furniture_id=furn)
            modules_tmp.extend(modules)
        for project in projects:
            consumables_tmp.extend(get_consumables(project_id=project))
            expeditions_tmp.extend(get_expeditions(project_id=project))
            group_tmp.extend(get_groups(project_id=project))
            parts = get_parts(project_id=project)
            parts_tmp.extend(parts)
            for part in parts:
                work_task_tmp.extend(get_workerTasks(part_id=part))
                machine_task_tmp.extend(get_machineTasks(part_id=part))
            assemblies = get_assemblies(project_id=project)
            assemblies_tmp.extend(assemblies)

    results['Budget'] = get_budgets(owner_id)
    results['Project'] = projects_tmp
    results['Consumable'] = consumables_tmp
    results['Expedition'] = expeditions_tmp
    results['Assembly'] = assemblies_tmp
    results['Furniture'] = furniture_tmp
    results['Module'] = modules_tmp
    results['Group'] = group_tmp
    results['Part'] = parts_tmp
    results['WorkTask'] = work_task_tmp
    results['MachineTask'] = machine_task_tmp
    return results


def convert_list_into_string(ids: list) -> str:
    ids_list = '\",\"'.join(ids)
    ids_list = '\"' + ids_list + '\"'
    return ids_list


def create_path(target: str, base_path: Optional[Union[str, None]] = None) -> bool:
    if base_path is None:
        base_path = settings.MEDIA_ROOT
    path = Path(base_path).resolve().joinpath(target)
    try:
        path.mkdir(exist_ok=True, parents=True)
        os.chown(path=path, uid=1001, gid=1001)
        os.chmod(path=path, mode=0o777)
        return True
    except Exception as error:
        logger.error(error)
        return False


def create_user_folder(user, base_path: Optional[Union[str, None]] = None) -> bool:
    target = f"mofreitas/clientes/{user.email.__str__()}/"
    return create_path(target=target, base_path=base_path)


def get_budget_owner(budget_id: str):
    from users.models import CustomerProfile
    from django.conf import settings
    from django.db.models import QuerySet
    import requests
    from utilities.client import oauth
    url: str = settings.ORION_ENTITIES + f'/{budget_id}/?options=keyValues'
    headers: dict = settings.ORION_HEADERS
    response = requests.get(url=url, headers=headers, auth=oauth)
    if response.status_code == 200:
        data = response.json()
        owner: str = data.get('orderBy', None)
        if owner:
            customer_id = owner.split(':')[-1]
            customers: QuerySet = CustomerProfile.objects.filter(id=customer_id)
            if customers.exists():
                return customers.first()


def create_sub_folders(parent, names: list) -> dict:
    folders = dict()
    for name in names:
        folders[name] = get_folder_or_create(parent.user, name, budget=parent.budget, parent=parent)
    return folders


def create_budget_folder(budget_id, base_path: Union[str, None] = None) -> bool:
    customer = get_budget_owner(budget_id=budget_id)
    name: str = get_budget_name(budget_id)
    proj_folder = get_folder_or_create(customer.user, name, budget=budget_id, parent=None)
    result = False
    try:
        logger.info("Trying to create budget folders")
        folders = create_sub_folders(parent=proj_folder, names=["project", "briefing"])
        create_sub_folders(parent=folders.get("project"), names=["EASM", "ALPHACAM"])
        create_sub_folders(parent=folders.get("briefing"), names=["Listas de Corte e Etiquetas", "3D", "VF do Cliente"])
        result = True
    except Exception as error:
        logger.error(f"The following exception occurred: \n {error}")
    finally:
        return result


def get_data(pk: str, params=None) -> Optional[dict]:
    response = get_entity(pk=pk, params=params)
    if response.status_code == 200:
        return json.loads(response.content.decode('unicode-escape'))


def get_from_furniture(furniture_id: str, attrs=None) -> List[Optional[Any]]:
    if attrs is None:
        attrs: str = 'hasBudget'
    params = dict(attrs=attrs)
    data = get_data(pk=furniture_id, params=params)
    if data:
        return [data.get(attr) for attr in attrs.split(',')]


def get_project_from_budget(budget_id: str) -> Optional[str]:
    data = get_data(pk=budget_id, params=dict(attrs='hasBudget'))
    if data:
        return data.get('hasBudget')


def get_folder(user, name, budget, parent, use_parent: bool = True):
    from bucket.models import Folder
    if use_parent:
        folders: QuerySet = Folder.objects.filter(user=user, name=name, budget=budget, parent=parent)
    else:
        folders: QuerySet = Folder.objects.filter(user=user, name=name, budget=budget)
    if folders.exists():
        return folders.first()


def get_valid_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.replace('/', '-')
    return name


def get_folder_or_create(user, name, budget, parent):
    from bucket.models import Folder
    name = get_valid_name(name=name)
    folders: QuerySet = Folder.objects.filter(user=user, name=name, budget=budget, parent=parent)
    if folders.exists():
        return folders.first()
    folder: Folder = Folder(user=user, name=name, budget=budget, parent=parent)
    folder.save()
    return folder


def update_folder(update_params: dict, query_params: dict):
    from bucket.models import Folder
    folders: QuerySet = Folder.objects.filter(**query_params)
    if folders.exists():
        folder = folders.first()
        for field in list(update_params):
            setattr(folder, field, update_params[field])


def delete_folder(user, name, budget, parent) -> bool:
    from bucket.models import Folder
    folders: QuerySet = Folder.objects.filter(user=user, name=name, budget=budget, parent=parent)
    if folders.exists():
        folders.first().delete()
        return True
    return False


def delete_folders_for_furniture(furniture_id: str) -> None:
    result = delete_folders_for_furniture_process(furniture_id)
    serializers.ValidationError(f"Error when delete the folder: {result}")


def delete_folders_for_furniture_process(furniture_id: str) -> bool:
    budget_id, furniture_type, name = get_from_furniture(furniture_id, attrs='hasBudget,furnitureType,name')
    if budget_id is None:
        return False
    customer = get_budget_owner(budget_id=budget_id)
    if customer is None:
        return False
    budget_folder = get_folder(customer.user, get_budget_name(budget_id), budget_id, parent=None)
    if budget_folder is None:
        return False
    project_folder = get_folder(customer.user, 'project', budget_id, parent=budget_folder)
    if project_folder is None:
        return False
    if furniture_type == FurnitureType.GROUP.value:
        return delete_folder(customer.user, name, budget=budget_id, parent=project_folder)
    elif furniture_type == FurnitureType.SUBGROUP.value:
        group_name = get_from_furniture(furniture_id, attrs='group')[0]
        group_folder = get_folder(customer.user, group_name, budget=budget_id, parent=project_folder)
        return delete_folder(customer.user, name=name, budget=budget_id, parent=group_folder)
    elif furniture_type == FurnitureType.FURNITURE.value:
        sub_group, group = get_from_furniture(furniture_id, attrs='subGroup,group')
        group_folder = get_folder(customer.user, group, budget=budget_id, parent=project_folder)
        sub_group_folder = get_folder(customer.user, sub_group, budget=budget_id, parent=group_folder)
        delete_folder(customer.user, name=name, budget=budget_id, parent=sub_group_folder)
    return False


def create_folders_for_furniture(furniture_id: str) -> bool:
    budget_id, furniture_type, name = get_from_furniture(furniture_id, attrs='hasBudget,furnitureType,name')
    if budget_id:
        customer = get_budget_owner(budget_id=budget_id)
        if customer:
            budget_folder = get_folder_or_create(customer.user, get_budget_name(budget_id), budget_id, parent=None)
            project_folder = get_folder_or_create(customer.user, 'project', budget_id, parent=budget_folder)
            if furniture_type == FurnitureType.GROUP.value:
                get_folder_or_create(customer.user, name, budget=budget_id, parent=project_folder)
            elif furniture_type == FurnitureType.SUBGROUP.value:
                group_name = get_from_furniture(furniture_id, attrs='group')[0]
                group_folder = get_folder_or_create(customer.user, group_name, budget=budget_id, parent=project_folder)
                get_folder_or_create(customer.user, name=name, budget=budget_id, parent=group_folder)
            elif furniture_type == FurnitureType.FURNITURE.value:
                sub_group, group = get_from_furniture(furniture_id, attrs='subGroup,group')
                group_folder = get_folder_or_create(customer.user, group, budget=budget_id, parent=project_folder)
                sub_group_folder = get_folder_or_create(customer.user, sub_group, budget=budget_id,
                                                        parent=group_folder)
                get_folder_or_create(customer.user, name=name, budget=budget_id, parent=sub_group_folder)
            else:
                return False
            return True
    return False


def update_folder_for_furniture(furniture_id: str, old_name: str) -> bool:
    budget_id, furniture_type, name = get_from_furniture(furniture_id, attrs='hasBudget,furnitureType,name')
    if budget_id:
        customer = get_budget_owner(budget_id=budget_id)
        if customer:
            budget_folder = get_folder_or_create(customer.user, get_budget_name(budget_id), budget_id, parent=None)
            project_folder = get_folder_or_create(customer.user, 'project', budget_id, parent=budget_folder)
            if furniture_type == FurnitureType.GROUP.value:
                update_folder(query_params=dict(name=old_name,
                                                parent=project_folder,
                                                user=customer.user,
                                                budget=budget_id
                                                ), update_params=dict(name=name))
                get_folder_or_create(customer.user, name, budget=budget_id, parent=project_folder)
            elif furniture_type == FurnitureType.SUBGROUP.value:
                group_name = get_from_furniture(furniture_id, attrs='group')[0]
                group_folder = get_folder_or_create(customer.user, group_name, budget=budget_id, parent=project_folder)
                update_folder(query_params=dict(name=old_name,
                                                parent=group_folder,
                                                user=customer.user,
                                                budget=budget_id
                                                ), update_params=dict(name=name))
            elif furniture_type == FurnitureType.FURNITURE.value:
                sub_group, group = get_from_furniture(furniture_id, attrs='subGroup,group')
                group_folder = get_folder_or_create(customer.user, group, budget=budget_id, parent=project_folder)
                sub_group_folder = get_folder_or_create(customer.user, sub_group, budget=budget_id,
                                                        parent=group_folder)
                update_folder(query_params=dict(name=old_name,
                                                parent=sub_group_folder,
                                                user=customer.user,
                                                budget=budget_id
                                                ), update_params=dict(name=name))

    return False


def validate_easm_file(file):
    if not file.name.lower().endswith('.easm'):
        raise serializers.ValidationError("Only EASM files are allowed.")
    return file


def validate_excel_file(file):
    if not file.name.lower().endswith('.xlsx'):
        raise serializers.ValidationError("Only xlsx files are allowed.")
    return file


def generate_path_hash(file_path, key, algorithm='sha256'):
    if algorithm not in hashlib.algorithms_guaranteed:
        raise ValueError("Invalid algorithm. Please use one of the following: {}".format(hashlib.algorithms_guaranteed))
    hash_obj = hmac.new(key.encode('utf-8'), file_path.encode('utf-8'), getattr(hashlib, algorithm))
    return hash_obj.hexdigest()


def get_budget_name(budget_id: str) -> str:
    name = budget_id
    if ':' in budget_id:
        name = budget_id.split(':')[-1]
        name = name.split('_')[-1]
    return name


def get_folder_path(obj) -> str:
    folder_path = ['mofreitas', 'clientes', obj.user.email.__str__()]
    current_folder = obj
    while current_folder is not None:
        folder_path.insert(3, current_folder.name)
        current_folder = current_folder.parent
    return "/".join(folder_path)


def get_file_path(obj) -> str:
    folder_path = ['mofreitas', 'clientes', obj.folder.user.email.__str__()]
    current_folder = obj.folder
    while current_folder is not None:
        folder_path.insert(3, current_folder.name)
        current_folder = current_folder.parent
    folder_path.append(obj.file_name)
    return obj.get_file_path()


def delete_budget_folder(budget_id: str):
    customer = get_budget_owner(budget_id=budget_id)
    name = get_budget_name(budget_id)
    if customer:
        delete_folder(customer.user, name, budget_id, parent=None)


def is_valid_sys_path(path: str) -> bool:
    """
    Determine if the given string is a valid system path.

    This function checks if the input string contains any invalid characters
    for a typical system path. Invalid characters are: '?', '*', ':', and '\\'.

    :param path: The string representing the system path to be validated.
    :return: True if the input string is a valid system path, otherwise False.
    """
    return not re.search(r'[?*:\\]', path)


def has_special_chars(name: str) -> bool:
    printable = set(string.printable)
    return any(char not in printable for char in name)


def update_folder_file_system(old_path, new_path, new_parent=None) -> bool:
    old_path = Path(settings.MEDIA_ROOT).joinpath(old_path)
    new_path = Path(settings.MEDIA_ROOT).joinpath(new_path)
    name_changed = old_path.name != new_path.name
    if new_parent is not None and not name_changed:
        from bucket.models import Folder
        parents = Folder.objects.filter(pk=new_parent.pk)
        if not parents.exists():
            msg = f"Fail to create folder, no parent folder found with the pk: '{new_parent}'"
            logger.warning(msg)
            raise ValidationError(msg)
        parent = parents.first()
        if old_path.exists() and not new_path.exists():
            shutil.move(old_path.__str__(), Path(settings.MEDIA_ROOT).joinpath(parent.path).__str__())
            return True
    if old_path.exists() and not new_path.exists() and name_changed:
        os.rename(old_path.__str__(), new_path.__str__())
        return True
    return True


def ends_with_slash(url: str) -> str:
    return url if url.endswith('/') else url + '/'


def remove_leading_slash(s: str) -> str:
    return s[1:] if s.startswith('/') else s


def build_url(url: str) -> str:
    from django.contrib.sites.models import Site
    current_site = Site.objects.get(name='backend')
    domain = current_site.domain
    return f"{ends_with_slash(domain)}{remove_leading_slash(url)}"
