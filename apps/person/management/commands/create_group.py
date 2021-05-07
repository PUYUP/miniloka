from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

GROUPS = ["Customer", "Owner", "Employee"]


class Command(BaseCommand):
    help = "Creates read only default permission groups for users"

    def handle(self, *args, **kwargs):
        for group in GROUPS:
            is_default = group == "Customer"
            new_group, created = Group.objects.get_or_create(
                name=group, is_default=is_default)

        print("Created default group.")
