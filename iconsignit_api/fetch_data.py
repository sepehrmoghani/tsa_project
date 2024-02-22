# myapp/management/commands/fetch_data.py

from django.core.management.base import BaseCommand
from iconsignit_api.views import DatabaseManagerView

class Command(BaseCommand):
    help = 'Fetch data from API and execute views.py function'

    def handle(self, *args, **kwargs):
        DatabaseManagerView()
        self.stdout.write(self.style.SUCCESS('Data fetched successfully'))
