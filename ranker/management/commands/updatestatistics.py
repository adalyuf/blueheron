from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ranker.models import Keyword, Statistic

class Command(BaseCommand):
    help = "Updates keyword statistics"

    # def add_arguments(self, parser):
    #     parser.add_argument('file_path', nargs=1, type=str) 
        #This is a positional argument, which, since added first, evaluates the first word to come after the command
        # The nargs='+' command says to take every word in the command and combine it together into a list and error if no words are found

    def handle(self, *args, **options):
        #handle is a special method that the django manage command will run, with the args and options provided

        # Consider wrapping each of these in a transaction.atomic and selecting with select_for_update()
        # Con is that it will lock the entire Keywords table for 3+ minutes, but will prevent keywords from being added/updated while stat is calculated

        print("Starting to update statistics. This historically takes around 3 minutes for each of the larger statistics.")

        #Update total keywords
        keywords_total = Keyword.objects.all().count()
        keywords_total_stat = Statistic.objects.get(key="keywords_total")
        keywords_total_stat.value = keywords_total
        keywords_total_stat.save()
        print(f"Total keywords updated. ({keywords_total_stat.value})")

        #Update available keywords
        keywords_available = Keyword.objects.filter(answered_at__isnull=True).filter(requested_at__isnull=True).count()
        keywords_available_stat = Statistic.objects.get(key="keywords_available")
        keywords_available_stat.value = keywords_available
        keywords_available_stat.save()
        print(f"Available keywords updated. ({keywords_available_stat.value})")

        #Update pending keywords
        keywords_pending = Keyword.objects.filter(answered_at__isnull=True).filter(requested_at__isnull=False).count()
        keywords_pending_stat = Statistic.objects.get(key="keywords_pending")
        keywords_pending_stat.value = keywords_pending
        keywords_pending_stat.save()
        print(f"Pending keywords updated. ({keywords_pending_stat.value})")

        #Update answered keywords
        keywords_answered = Keyword.objects.filter(answered_at__isnull=False).count()
        keywords_answered_stat = Statistic.objects.get(key="keywords_answered")
        keywords_answered_stat.value = keywords_answered
        keywords_answered_stat.save()
        print(f"Keywords answered updated. ({keywords_answered_stat.value})")



