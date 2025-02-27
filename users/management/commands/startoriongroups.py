from django.core.management.base import BaseCommand, CommandError
from permissions.models import Permission, Group
from django.conf import settings


def get_codenames(schema: dict) -> list:
    tmp = list()
    for model, actions in schema.items():
        tmp.extend([f"{action}_{model}" for action in actions])
    return tmp


class Command(BaseCommand):
    help = 'Creates groups with permissions'

    @staticmethod
    def create_all_permissions():
        codenames = get_codenames(schema=settings.ORION_ALL_PERMISSIONS)
        for codename in codenames:
            Permission.objects.create(name=codename, codename=codename)

    def delete_all_groups(self):
        self.stdout.write(self.style.WARNING("Deleting all groups and Permissions..."))
        Permission.objects.all().delete()
        Group.objects.all().delete()

    def get_permissions(self, codenames) -> list:
        perms = list()
        for codename in codenames:
            try:
                perm = Permission.objects.get(codename=codename)
                perms.append(perm.id)
            except Exception as error:
                self.stdout.write(self.style.ERROR(error))
        return perms

    def create_group(self, schema: dict, name: str = 'Organizations') -> Group:
        group: Group = Group.objects.create(name=name)
        permissions = self.get_permissions(codenames=get_codenames(schema=schema))
        for permission in permissions:
            group.permissions.add(permission)
        return group

    def create_organization_group(self) -> Group:
        return self.create_group(schema=settings.ORION_ADMIN, name='Organizations')

    def create_worker_group(self) -> Group:
        return self.create_group(schema=settings.ORION_WORKER, name='Workers')

    def create_customer_group(self) -> Group:
        return self.create_group(schema=settings.ORION_CUSTOMER, name='Customers')

    def add_arguments(self, parser):
        parser.add_argument(
            '-y', '--yes',
            action='store_true',
            dest='yes',
            help='Do not prompt for confirmation, just delete all groups and create new ones.'
        )

    def handle(self, *args, **options):
        answer = 'yes' if options['yes'] else None

        if answer is None:
            answer = input(
                'To create new groups, old one will be deleted \n Are you sure you want to delete all groups? '
                '(yes/no) ')
        if answer.lower() == 'yes':
            # Delete all groups
            self.delete_all_groups()
            self.stdout.write(self.style.SUCCESS('Groups deleted successfully.'))
            self.create_all_permissions()
            self.create_organization_group()
            self.create_worker_group()
            self.create_customer_group()
            self.stdout.write(self.style.SUCCESS("Groups created successfully."))
        elif answer.lower() == 'no':
            self.stdout.write(self.style.WARNING('Aborted. No groups were deleted.'))
        else:
            raise CommandError('Invalid input. Please enter "yes" or "no".')
