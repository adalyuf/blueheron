from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone, html

from ranker.models import Domain, TokenType, Token, Template, TemplateItem, Conversation, Message, KeywordFile, Keyword, KeywordPosition
from ranker.tasks import call_openai, save_keyword_response

import os, openai, markdown, json, csv

import asyncio
import concurrent.futures              # Allows creating new processes
from math import ceil, floor           # Helps divide up our requests evenly across our CPU cores
from multiprocessing import cpu_count  # Returns our number of CPU cores
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

class Command(BaseCommand):
    help = "Import keywords from all primary files that have not yet been processed."

    def add_arguments(self, parser):
        parser.add_argument('--kwfile', action='store', type=int)


    def handle(self, *args, **options):
        start_time = timezone.now()

        if options['kwfile']:
            files = KeywordFile.objects.filter(id__exact=options['kwfile']).filter(primary=True).filter(processed_at=None)
        else:
            files = KeywordFile.objects.filter(primary=True).filter(processed_at=None)

        for myfile in files:
            domain = myfile.domain
            file_start = timezone.now()

            #Read in Keywords from file
            with myfile.filepath.open(mode='r') as csvfile:
                item_list = []
                reader = csv.DictReader(csvfile)
                for row in reader:
                    item = Keyword( 
                        keyword = row['Keyword'],
                    )
                    item_list.append(item)
                Keyword.objects.bulk_create(item_list, ignore_conflicts=True)

                self.stdout.write(f"Bulk insert completed: {len(item_list)} {type(item_list[0]).__name__} records")

            #Save original data in case useful later
            keyword_position_list = []
            with myfile.filepath.open(mode='r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    keyword = Keyword.objects.get(keyword = row['Keyword'])
                    try:
                         retrieved_at = timezone.make_aware(row['Timestamp'], timezone=timezone.utc)
                    except:
                         retrieved_at = timezone.now()
                    keyword_position = KeywordPosition(
                        domain      = domain,
                        keyword     = keyword,
                        domain_text = domain.domain,
                        keyword_text        = row['Keyword'],
                        position            = row['Position'],
                        previous_position   = row['Previous position'],
                        search_volume       = row['Search Volume'],
                        keyword_difficulty  = row['Keyword Difficulty'],
                        cpc                 = row['CPC'],
                        url                 = row['URL'],
                        traffic             = row['Traffic'],
                        traffic_percent     = row['Traffic (%)'],
                        traffic_cost        = row['Traffic Cost'],
                        competitive_difficulty = row['Competition'],
                        results             = row['Number of Results'],
                        trends              = row['Trends'],
                        retrieved_at        = retrieved_at,
                        serp                = row['SERP Features by Keyword'],
                        intents             = row['Keyword Intents'],
                        type                = row['Position Type'],
                    )
                    keyword_position_list.append(keyword_position)
                    if len(keyword_position_list) > 5000:
                        KeywordPosition.objects.bulk_create(keyword_position_list, ignore_conflicts=True)
                        self.stdout.write(f"Bulk insert completed: {len(keyword_position_list)} records")
                        keyword_position_list = []
                if keyword_position_list:
                        KeywordPosition.objects.bulk_create(keyword_position_list, ignore_conflicts=True)
                self.stdout.write(f"Bulk upsert completed: {len(keyword_position_list)} records")
            
            file_stop = timezone.now()
            myfile.processed_at = file_stop
            myfile.save()
            self.stdout.write(f"Loading {myfile.filepath.name} took: {(file_stop-file_start).total_seconds()} seconds.")

        end_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f"Loading all {len(files)} files took: {(end_time-start_time).total_seconds()} seconds."
            )
        )

        