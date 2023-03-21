from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ranker.models import Domain

import csv

class Command(BaseCommand):
    help = "import a list of domains at first launch"

    def add_arguments(self, parser):
        parser.add_argument('file_path', nargs=1, type=str) 
        #This is a positional argument, which, since added first, evaluates the first word to come after the command
        # The nargs='+' command says to take every word in the command and combine it together into a list and error if no words are found

    def handle(self, *args, **options):
        #handle is a special method that the django manage command will run, with the args and options provided

        if Domain.objects.count() > 0:
            self.stderr.write(f"There are already {Domain.objects.count()} domains in the database. Skipping import.")
            return

        myfile = options["file_path"][0]
        start_time = timezone.now()

        with open(myfile, "r") as csv_file: #with replaces a try/finally syntax and ensures all files that are opened are closed and resources released.
            data = csv.reader(csv_file, delimiter=",")
            domains = []
            next(data) #Skip header row
            for row in data:
                domain = Domain(
                    rank=row[0],
                    domain=row[1],
                    keywords=row[2],
                    traffic=row[3],
                    cost=row[4],
                )
                domains.append(domain)
                if len(domains) > 5000:
                    Domain.objects.bulk_create(domains)
                    self.stdout.write(f"Bulk upload completed: {len(domains)} records")
                    domains = []
            if domains:
                Domain.objects.bulk_create(domains)
                self.stdout.write(f"Bulk upload completed: {len(domains)} records")
        
        end_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f"Loading CSV took: {(end_time-start_time).total_seconds()} seconds."
            )
        )