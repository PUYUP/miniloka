from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

GROUPS = ["Customer", "Assistant"]


class Command(BaseCommand):
	help = "Creates read only default permission groups for users"
	
	def handle(self, *args, **kwargs):
		for group in GROUPS:
			new_group, created = Group.objects.get_or_create(name=group)
		
		print("Created default group.")
