from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ranker.models import Brand, BrandKeyword, Keyword

import csv

class Command(BaseCommand):
    help = "import a list of domains at first launch"

    def add_arguments(self, parser):
        parser.add_argument('--batch', action='store', type=int)

        # parser.add_argument('file_path', nargs=1, type=str) 
        #This is a positional argument, which, since added first, evaluates the first word to come after the command
        # The nargs='+' command says to take every word in the command and combine it together into a list and error if no words are found

    def handle(self, *args, **options):
        #handle is a special method that the django manage command will run, with the args and options provided

        batch_size = options["batch"]
        print(f'Batch size: {batch_size}')
        brand_list = Brand.objects.filter(keyword_indexed_at__isnull=True)[:batch_size]
        print(f"Found {len(brand_list)} brands")
        i = 0
        for brand in brand_list:
            i += 1
            start_time = timezone.now()
            keyword_list = Keyword.objects.filter(ai_answer__icontains=brand.brand)
            if keyword_list:
                brand.keyword.add(*keyword_list)
            # for keyword in keyword_list:
            #     brand.keyword.add(keyword)
            brand.keyword_indexed_at = timezone.now()
            brand.save()
            end_time = timezone.now()
            print(f"({i}/{len(brand_list)} - {int((end_time-start_time).total_seconds())} sec - {timezone.now()}) Brand ID {brand.pk} ({brand.brand}): {len(keyword_list)} keywords updated")