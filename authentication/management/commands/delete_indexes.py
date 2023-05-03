from django.core.management.base import BaseCommand
from authentication.models import PdfDocument, Vectorstore

class Command(BaseCommand):
    help = 'Deletes all rows in PineconeIndex model'

    def handle(self, *args, **options):
        Vectorstore.objects.all().delete()
        PdfDocument.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all PineconeIndex rows'))
