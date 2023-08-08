from django.core.management import call_command
from django.utils import timezone, html
from django.conf import settings
from celery import shared_task
import os, openai, markdown, json, re, tldextract, requests

from ranker.models import Message, Keyword, Domain, Brand, BrandKeyword
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 8}, rate_limit='1500/m')
def call_openai(self, prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    message_array = [{"role": "system", "content": "You are a helpful assistant."}] #by using async we forgo ability to have each message be dependent on previous messages and there is no guarantee of time order
    message_array.append({"role": "user", "content": prompt})
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=message_array, temperature=0.6,)
    except openai.error.APIError as e:
        #Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
        logger.warning("OpenAI API returned an API Error: %s", e)
        raise e 
    except openai.error.APIConnectionError as e: 
        #Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        logger.warning("Failed to connect to OpenAI API: %s", e)
        raise e 
    except openai.error.RateLimitError as e:
        #Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        logger.warning("OpenAI API request exceeded rate limit: %s", e)
        raise e 
    try:
        return response['choices'][0]['message']['content']
    except:
        print(f"Couldn't get a response. We retried several times. Sorry. Better luck next time.")
        logger.warning("Multiple attempts failed, response: %s", response)
        raise "Multiple retries attempted, all failed."


@shared_task(queue="express")
def save_message_response(response, message_id):
    message = Message.objects.get(id = message_id)
    try:
        message.response = response
        if message.template_item.mode == 'markdown':
            try: 
                message.markdown_response = html.format_html(markdown.markdown(message.response, extensions=['tables']))
            except:
                print("Error saving as markdown. Did you mean to save as JSON?")
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
        print(f"Message: {message.prompt} took {(message.answered_at-message.requested_at).total_seconds()} seconds.")
    except:
        message.requested_at = None
        message.save()
        print(f"Couldn't get response from OpenAI API. Resetting requested_at to null.")
    conversation = message.conversation
    if (conversation.message_set.filter(answered_at__isnull=False).count() > 0 & conversation.message_set.filter(answered_at=None).count() == 0):
        conversation.answered_at = timezone.now()
        conversation.save()

@shared_task(queue="express")
def save_keyword_response(api_response, keyword_id):
    keyword = Keyword.objects.get(id = keyword_id)
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
        print(f"{keyword} took {(keyword.answered_at-keyword.requested_at).total_seconds()} seconds.")
        return "Keyword saved"
    except:
        print("Couldn't assign response to columns. Resetting requested_at to null.")
        keyword.requested_at = None
        keyword.save()
        return "Keyword not saved"

@shared_task(queue="express")
def save_business_json(api_response, domain_id):
    domain = Domain.objects.get(id = domain_id)
    domain.business_api_response = api_response
    domain.save()
    try:
        start_pos   = api_response.find('{')
        end_pos     = api_response.rfind('}')
        json_string = api_response[start_pos:end_pos+1]
        json_object = json.loads(json_string)

        domain.business_json = json_object

        domain.business_name    = domain.business_json['business_name']
        domain.naics_6          = domain.business_json['naics_6']

        for brand in domain.business_json['company_brands']:
            # lowercase, try to pull the brand, if fail, add brand
            # Add domain to brand once established
            brand = brand.lower()
            try:
                our_brand = Brand.objects.get(brand=brand)
            except:
                our_brand = Brand(brand=brand)
                print(f"Couldn't find {brand}, adding to database.")
                our_brand.save()
            our_brand.domain.add(domain, through_defaults={'type': 'brand'})
            

        for brand in domain.business_json['company_products']:
            #TODO: If this becomes more complicated, try and DRY this up with above.
            brand = brand.lower()
            try:
                our_brand = Brand.objects.get(brand=brand)
            except:
                our_brand = Brand(brand=brand)
                print(f"Couldn't find {brand}, adding to database.")
                our_brand.save()
            our_brand.domain.add(domain, through_defaults={'type': 'product'})

        for orig_comp_domain in domain.business_json['competitor_domains']:
            try:
                comp_domain = tldextract.extract(orig_comp_domain).registered_domain

                try:
                    competitor = Domain.objects.get(domain=comp_domain)
                except:
                    print(f"Couldn't find match: {orig_comp_domain} - skipping.")

                domain.competitors.add(competitor)

            except:
                print(f"Couldn't find matching competitor domain: {orig_comp_domain} for source domain: {domain.domain}")
        
        domain.save()
    except Exception as e:
        print("Couldn't save business json.")
        domain.business_api_response = f"ERROR: Couldn't save business json: {repr(e)}."
        domain.save()


@shared_task(queue="steamroller")
def index_brand(batch_size):
    print(f'Batch size: {batch_size}')
    brand_list = Brand.objects.filter(indexing_requested_at__isnull=True).filter(keyword_indexed_at__isnull=True)[:batch_size]
    print(f"Found {len(brand_list)} brands")

    for brand in brand_list:
        brand.indexing_requested_at = timezone.now()
    Brand.objects.bulk_update(brand_list, ['indexing_requested_at'])

    i = 0
    for brand in brand_list:
        i += 1
        start_time = timezone.now()
        keyword_list = Keyword.objects.filter(ai_answer__icontains=brand.brand)
        if keyword_list:
            brand.keyword.add(*keyword_list)
        brand.keyword_indexed_at = timezone.now()
        brand.save()
        end_time = timezone.now()
        print(f"({i}/{len(brand_list)} - {int((end_time-start_time).total_seconds())} sec - {timezone.now()}) Brand ID {brand.pk} ({brand.brand}): {len(keyword_list)} keywords updated")


@shared_task(queue="steamroller")
def refill_keyword_queue():
    if os.getenv("ENVIRONMENT") == "production":
        kw_batch_size = 10000
        max_queue = 270000
    else:
        kw_batch_size = 100
        max_queue = 300

    kw_batch_size = kw_batch_size
    queued = Keyword.objects.filter(answered_at__isnull=True).filter(requested_at__isnull=False).count()

    if queued + kw_batch_size >= max_queue:
        kw_batch_size = max(max_queue-queued, 0)
    
    keyword_list = Keyword.objects.filter(requested_at=None)[:kw_batch_size]
    logger.info(f"Requesting responses for {kw_batch_size} keywords.")

    item_list = []
    for keyword in keyword_list:
        keyword.requested_at = timezone.now()
        item_list.append(keyword)
    Keyword.objects.bulk_update(item_list, ["requested_at"], batch_size=5000)

    for keyword in keyword_list:
        prompt = "If a user searches for @currentKeyword, what is their user intent, how would you rephrase this as a natural language question, please provide a thorough and detailed answer to the natural language question, what was their likely previous query, and what could be their next query? Provide your response as a simple JSON object, with keys \"user_intent\", \"natural_language_question\", \"ai_answer\", \"likely_previous_queries\", and \"likely_next_queries\". If this is likely to be their first or last query in their journey, answer \"none\" in the field"
        prompt = prompt.replace("@currentKeyword", keyword.keyword)
        call_openai.apply_async( (prompt,), link=save_keyword_response.s(keyword.id)) #note the comma in arguments, critical to imply tuple, otherwise thinks array, passes response as first argument
 