from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from owl.models import Domain, TokenType, Token

import csv

class Command(BaseCommand):
    help = "import a list of domains at first launch"

    # def add_arguments(self, parser):
    #     parser.add_argument('file_path', nargs=1, type=str) 

    def handle(self, *args, **options):

        if TokenType.objects.filter(type='domain').count() == 0:
            t = TokenType(type='domain')
            t.save()
            self.stdout.write(f"Created TokenType {t.type}")
            
        t = TokenType.objects.filter(type='domain').first()
        
        if t.token_set.count() > 0:
            self.stderr(f"There are already {t.token_set.count()} domain tokens, skipping tokenization")
            return

        tokens = []
        domains = Domain.objects.all()

        for d in domains:
            token = Token(
                value = d.domain,
                type = t
            )
            tokens.append(token)

        Token.objects.bulk_create(tokens)
        self.stdout.write(f"Tokenized: {len(tokens)} domains")


