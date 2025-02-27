from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.conf import settings


def get_codenames(schema: dict) -> list:
    tmp = list()
    for model, actions in schema.items():
        tmp.extend([f"{action}_{model}" for action in actions])
    return tmp


class Command(BaseCommand):
    help = 'Creates groups with permissions'

    def delete_all_groups(self):
        self.stdout.write(self.style.WARNING("Deleting all groups..."))
        Group.objects.all().delete()

    def get_permissions(self, codenames) -> list:
        permissions = list()
        for codename in codenames:
            try:
                perms = Permission.objects.filter(codename=codename)
                if perms and perms.__len__() != 1:
                    perms = perms.filter(content_type__app_label='auth')
                perm = perms.first()
                permissions.append(perm.id)
            except Exception as error:
                self.stdout.write(self.style.ERROR(error))
        return permissions

    def create_group(self, schema: dict, name: str = 'Organizations') -> Group:
        group: Group = Group.objects.create(name=name)
        permissions = self.get_permissions(codenames=get_codenames(schema=schema))
        for permission in permissions:
            group.permissions.add(permission)
        return group

    def create_organization_group(self) -> Group:
        return self.create_group(schema=settings.ADMIN, name='Organizations')

    def create_worker_group(self) -> Group:
        return self.create_group(schema=settings.WORKER, name='Workers')

    def create_customer_group(self) -> Group:
        return self.create_group(schema=settings.CUSTOMER, name='Customers')

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
            self.delete_all_groups()
            self.stdout.write(self.style.SUCCESS('Groups deleted successfully.'))
            self.create_organization_group()
            self.create_worker_group()
            self.create_customer_group()
            self.stdout.write(self.style.SUCCESS("Groups created successfully."))

        elif answer.lower() == 'no':
            self.stdout.write(self.style.WARNING('Aborted. No groups were deleted.'))
            return
        else:
            raise CommandError('Invalid input. Please enter "yes" or "no".')






