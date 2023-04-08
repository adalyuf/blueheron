from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone, html

from ranker.models import Domain, TokenType, Token, Template, TemplateItem, Conversation, Message

import os, openai, markdown, json

import asyncio
import concurrent.futures              # Allows creating new processes
from math import ceil, floor           # Helps divide up our requests evenly across our CPU cores
from multiprocessing import cpu_count  # Returns our number of CPU cores
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

def return_last_value(retry_state):
    """return the result of the last call attempt"""
    return retry_state.outcome.result()

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6), retry_error_callback=return_last_value)
def call_openai(prompt, proc_num):
    message_array = [{"role": "system", "content": "You are a helpful assistant."}] #by using async we forgo ability to have each message be dependent on previous messages and there is no guarantee of time order
    message_array.append({"role": "user", "content": prompt})
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=message_array, temperature=0.6,)
    except openai.error.APIError as e:
        #Handle API error here, e.g. retry or log
        print(f"[Process {proc_num}] OpenAI API returned an API Error: {e}")
        pass
    except openai.error.APIConnectionError as e:
        #Handle connection error here
        print(f"[Process {proc_num}] Failed to connect to OpenAI API: {e}")
        pass
    except openai.error.RateLimitError as e:
        #Handle rate limit error (we recommend using exponential backoff)
        print(f"[Process {proc_num}] OpenAI API request exceeded rate limit: {e}")
        pass
    try:
        return response
    except:
        print(f"Couldn't get a response. We retried several times. Sorry. Better luck next time.")

def get_response(message, proc_num):
    message.requested_at = timezone.now()
    try:
        response = call_openai(message.prompt, proc_num)
        message.response = response['choices'][0]['message']['content']
        if message.template_item.mode == 'markdown':
            message.markdown_response = html.format_html(markdown.markdown(message.response, extensions=['tables']))
        elif message.template_item.mode == 'json':
            try:
                start_pos   = message.response.find('{')
                end_pos     = message.response.rfind('}')
                json_string = message.response[start_pos:end_pos+1]
                json_object = json.loads(json_string)
                message.json_response = json_object
            except:
                print("Error in json parsing.")
        message.answered_at = timezone.now()
        message.save()
        print(f"[Process {proc_num}] Message: {message.prompt} took {(message.answered_at-message.requested_at).total_seconds()} seconds.")
    except:
        message.requested_at = None
        message.save()
        print(f"Couldn't get response from OpenAI API. Resetting requested_at to null.")

def start_run(messages, proc_num):
    print(f"Starting process {proc_num} with {len(messages)} messages")
    for message in messages:
        get_response(message, proc_num)

def run_in_parallel(messages):
    futures = []
    if cpu_count() > len(messages):
        NUM_CORES = len(messages)
    else: 
        NUM_CORES = cpu_count()

    if len(messages) == 1:
        chunksize = 1
    else:
        chunksize =int(floor(len(messages) / (NUM_CORES-1)))

    with concurrent.futures.ProcessPoolExecutor(NUM_CORES) as executor:
        for core in range(NUM_CORES-1):
            new_future = executor.submit(
                start_run, # Function to perform
                # v Arguments v
                messages=messages[chunksize*core : chunksize*(core+1)],
                proc_num=core
            )
            futures.append(new_future)
        new_future = executor.submit(
            start_run, # Function to perform
            # v Arguments v
            messages=messages[chunksize*(NUM_CORES-1): ], #last process to pick up the remainder
            proc_num=NUM_CORES
        )

    results = [future.result() for future in concurrent.futures.as_completed(futures)]
    return results

class Command(BaseCommand):
    help = "Get responses for every message"

    def add_arguments(self, parser):
        parser.add_argument('--start', nargs=1, type=int)
        parser.add_argument('--end', nargs=1, type=int) 
        parser.add_argument('--conversation', action='store', type=int)
        parser.add_argument('--template', action='store', type=int)


    def handle(self, *args, **options):
        openai.api_key = os.getenv("OPENAI_API_KEY")

        if options['template']:
            template = Template.objects.get(id = options['template'])
            conversations = template.conversation_set.all()
        elif options['conversation']:
            conversations = Conversation.objects.filter(id__exact=options['conversation'])
        elif options['start'] and options['end']:
            conversations = Conversation.objects.filter(answered_at__isnull=True)[options["start"][0]:options["end"][0]]
        else:
            print("Command needs either --conversation, --template, or --start and --end arguments")
            return

        print(f"Processing {len(conversations)} conversations")
        messages = Message.objects.filter(conversation__in=conversations).filter(answered_at__isnull=True)
        if len(messages) == 0:
            print("All messages have already been processed, canceling operation.")
            return

        print(f"Processing {len(messages)} messages")

        start_time = timezone.now()

        for conversation in conversations:
            conversation.requested_at = start_time
        Conversation.objects.bulk_update(conversations, ['requested_at'])


        messages = run_in_parallel(messages)
            
            
        end_time = timezone.now()
        for conversation in conversations:
            conversation.answered_at = end_time
        Conversation.objects.bulk_update(conversations, ['answered_at'])

        self.stdout.write(
            self.style.SUCCESS(
                f"Getting responses took: {(end_time-start_time).total_seconds()} seconds."
            )
        )


