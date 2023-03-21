from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone, html

from ranker.models import Domain, TokenType, Token, Product, ProductTemplate, Conversation, Message

import os, openai, markdown

import asyncio

async def getresponse(message):
    message.requested_at = timezone.now()
    message_array = [{"role": "system", "content": "You are a helpful assistant."}] #by using async we forgo ability to have each message be dependent on previous messages and there is no guarantee of time order
    message_array.append({"role": "user", "content": message.prompt})
    o = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=message_array, temperature=0.6,)
    message.response = o['choices'][0]['message']['content']
    message.formatted_response = html.format_html(markdown.markdown(message.response, extensions=['tables']))
    message.answered_at = timezone.now()
    print(f"Message: {message.prompt} took {(message.answered_at-message.requested_at).total_seconds()} seconds.")

async def get_conversations(messages):
    async with asyncio.TaskGroup() as tg:
        for message in messages:
            tg.create_task(getresponse(message))
    return messages
    # The await is implicit when the context manager exits.

class Command(BaseCommand):
    help = "Get responses for every message"

    # def add_arguments(self, parser):
    #     parser.add_argument('file_path', nargs=1, type=str) 

    def handle(self, *args, **options):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        start_time = timezone.now()

        conversations = Conversation.objects.filter(answered_at__isnull=True)[30:35]
        print(f"Processing {len(conversations)} conversations")
        messages = Message.objects.filter(conversation__in=conversations).filter(answered_at__isnull=True)
        print(f"Processing {len(messages)} messages") #this print statement surprisingly important, forces evaluation of the query statement above, preventing it from being sent to the async function which cant handle querysets

        messages = asyncio.run(get_conversations(messages))
            
        Message.objects.bulk_update(messages, ['response','formatted_response', 'requested_at', 'answered_at'])
        end_time = timezone.now()
        for conversation in conversations:
            conversation.requested_at = start_time
            conversation.answered_at = end_time
        Conversation.objects.bulk_update(conversations, ['requested_at', 'answered_at'])

        self.stdout.write(
            self.style.SUCCESS(
                f"Getting responses took: {(end_time-start_time).total_seconds()} seconds."
            )
        )


