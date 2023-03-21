from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone, html

from ranker.models import Domain, TokenType, Token, Product, ProductTemplate, Conversation, Message

import os, openai, markdown

class Command(BaseCommand):
    help = "Get responses for every message"

    # def add_arguments(self, parser):
    #     parser.add_argument('file_path', nargs=1, type=str) 

    def handle(self, *args, **options):
        openai.api_key = os.getenv("OPENAI_API_KEY")

        conversations = Conversation.objects.filter(answered_at__isnull=True)[20:25]
        self.stdout.write(f"Processing {len(conversations)} conversations")

        start_time = timezone.now()

        for conversation in conversations:
            messages =  conversation.message_set.filter(answered_at__isnull=True)
            conversation.requested_at = timezone.now()
            self.stdout.write(f"Processing {len(messages)} messages")
            message_array = [{"role": "system", "content": "You are a helpful assistant."}]
            for message in messages:
                message.requested_at = timezone.now()
                message_array.append({"role": "user", "content": message.prompt})
                o = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=message_array, temperature=0.6,)
                message.response = o['choices'][0]['message']['content']
                # message_array.append({"role": "assistant", "content": message.response})
                message.formatted_response = html.format_html(markdown.markdown(message.response, extensions=['tables']))
                # message.save()
                message.answered_at = timezone.now()
                # self.stdout.write(f"Message: {message.prompt} took {(message.answered_at-message.requested_at).total_seconds()} seconds.")
            Message.objects.bulk_update(messages, ['response','formatted_response', 'requested_at', 'answered_at'])
            conversation.answered_at = timezone.now()
            conversation.save()

        end_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f"Getting responses took: {(end_time-start_time).total_seconds()} seconds."
            )
        )

        #Performance notes: saving for each response, for 10 conversations * 13 messages: 408 seconds
        # Removing response feedback: 307 seconds
        # Bulk updating each conversation's messages: 271s

        # Tokens used with feedback: 22,000
        # Tokens used without feedback: 4,000

