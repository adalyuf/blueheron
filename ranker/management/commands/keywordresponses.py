from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone, html

from ranker.models import Domain, TokenType, Token, Template, TemplateItem, Conversation, Message, KeywordFile, Keyword, KeywordPosition

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

#does not need to be modified when copy/pasting
def return_last_value(retry_state):
    """return the result of the last call attempt"""
    return retry_state.outcome.result()

#does not need to be modified when copy/pasting
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

#Modify this function when changing
def get_response(keyword, proc_num):
    keyword.requested_at = timezone.now()
    prompt = "If a user searches for @currentKeyword, what is their user intent, how would you rephrase this as a natural language question, please answer the natural language question, what was their likely previous query, and what could be their next query? Provide your response as a simple JSON object, with keys \"user_intent\", \"natural_language_question\", \"ai_answer\", \"likely_previous_queries\", and \"likely_next_queries\". If this is likely to be their first or last query in their journey, answer \"none\" in the field"
    prompt = prompt.replace("@currentKeyword", keyword.keyword)

    try:
        response = call_openai(prompt, proc_num)
        api_response = response['choices'][0]['message']['content']
        try:
            start_pos   = api_response.find('{')
            end_pos     = api_response.rfind('}')
            json_string = api_response[start_pos:end_pos+1]
            json_object = json.loads(json_string)

            keyword.json_response = json_object
 
            keyword.user_intent                 = keyword.json_response['user_intent']
            keyword.natural_language_question   = keyword.json_response['natural_language_question']
            keyword.ai_answer                   = keyword.json_response['ai_answer']
            keyword.likely_previous_queries     = keyword.json_response['likely_previous_queries']
            keyword.likely_next_queries         = keyword.json_response['likely_next_queries']

            keyword.answered_at = timezone.now()
            keyword.save()
            print(f"[Process {proc_num}] Message: {keyword} took {(keyword.answered_at-keyword.requested_at).total_seconds()} seconds.")
        except:
            print("Couldn't assign response to columns. Resetting requested_at to null.")
            keyword.requested_at = None
            keyword.save()
    except:
        keyword.requested_at = None
        keyword.save()
        print(f"Couldn't get response from OpenAI API. Resetting requested_at to null.")

#does not need to be modified when copy/pasting
def start_run(obj_list, proc_num):
    print(f"Starting process {proc_num} with {len(obj_list)} {type(obj_list[0]).__name__} objects")
    for keyword in obj_list:
        get_response(keyword, proc_num)

#does not need to be modified when copy/pasting
def run_in_parallel(obj_list):
    futures = []
    if cpu_count() > len(obj_list):
        NUM_CORES = len(obj_list)
    else: 
        NUM_CORES = cpu_count()

    if len(obj_list) == 1:
        chunksize = 1
    else:
        chunksize =int(floor(len(obj_list) / (NUM_CORES-1)))

    with concurrent.futures.ProcessPoolExecutor(NUM_CORES) as executor:
        for core in range(NUM_CORES-1):
            new_future = executor.submit(
                start_run, # Function to perform
                # v Arguments v
                obj_list=obj_list[chunksize*core : chunksize*(core+1)],
                proc_num=core
            )
            futures.append(new_future)
        new_future = executor.submit(
            start_run, # Function to perform
            # v Arguments v
            obj_list=obj_list[chunksize*(NUM_CORES-1): ], #last process to pick up the remainder
            proc_num=NUM_CORES
        )

    results = [future.result() for future in concurrent.futures.as_completed(futures)]
    return results

class Command(BaseCommand):
    help = "Import keywords from all primary files that have not yet been processed."

    def add_arguments(self, parser):
        parser.add_argument('--number', action='store', type=int)

    def handle(self, *args, **options):
        #When we switch to using a queue like celery, switch this to requested_at so the queues can know not to pick up one that is being worked by another
        if options['number']:
            keyword_list = Keyword.objects.filter(answered_at=None)[:options['number']]
        else:
            keyword_list = Keyword.objects.filter(answered_at=None)

        openai.api_key = os.getenv("OPENAI_API_KEY")

        if len(keyword_list) == 0:
            print("All messages have already been processed, canceling operation.")
            return
        print(f"Processing {len(keyword_list)} keywords")

        start_time = timezone.now()

        run_in_parallel(keyword_list)
                      
        end_time = timezone.now()

        self.stdout.write(
            self.style.SUCCESS(
                f"Getting responses took: {(end_time-start_time).total_seconds()} seconds."
            )
        )