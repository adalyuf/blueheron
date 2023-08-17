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

        #Update total keywords
        keywords_total = Keyword.objects.all().count()
        keywords_total_stat = Statistic.objects.get(key="keywords_total")
        keywords_total_stat.value = keywords_total
        keywords_total_stat.save()

        #Update available keywords
        keywords_available = Keyword.objects.filter(answered_at__isnull=True).filter(requested_at__isnull=True).count()
        keywords_available_stat = Statistic.objects.get(key="keywords_available")
        keywords_available_stat.value = keywords_available
        keywords_available_stat.save()

        #Update pending keywords
        keywords_pending = Keyword.objects.filter(answered_at__isnull=True).filter(requested_at__isnull=False).count()
        keywords_pending_stat = Statistic.objects.get(key="keywords_pending")
        keywords_pending_stat.value = keywords_pending
        keywords_pending_stat.save()

        #Update answered keywords
        keywords_answered = Keyword.objects.filter(answered_at__isnull=False).count()
        keywords_answered_stat = Statistic.objects.get(key="keywords_answered")
        keywords_answered_stat.value = keywords_answered
        keywords_answered_stat.save()



