from django.core.management import call_command
from django.utils import timezone, html
from celery import shared_task
import os, openai, markdown, json, re

from ranker.models import Message, Keyword, Domain, Brand

def return_last_value(retry_state):
        """return the result of the last call attempt"""
        return retry_state.outcome.result()

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 5})
def call_openai(self, prompt):
    openai.api_key = os.getenv("BACKUP_OPENAI_API_KEY")
    message_array = [{"role": "system", "content": "You are a helpful assistant."}] #by using async we forgo ability to have each message be dependent on previous messages and there is no guarantee of time order
    message_array.append({"role": "user", "content": prompt})
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=message_array, temperature=0.6,)
    except openai.error.APIError as e:
        #Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
        pass
    except openai.error.APIConnectionError as e:
        #Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        pass
    except openai.error.RateLimitError as e:
        #Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        pass
    try:
        return response['choices'][0]['message']['content']
    except:
        print(f"Couldn't get a response. We retried several times. Sorry. Better luck next time.")



# @shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 5})
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
    except:
        print("Couldn't assign response to columns. Resetting requested_at to null.")
        keyword.requested_at = None
        keyword.save()

@shared_task(queue="express")
def save_business_json(api_response, domain_id):
    domain = Domain.objects.get(id = domain_id)
    try:
        start_pos   = api_response.find('{')
        end_pos     = api_response.rfind('}')
        json_string = api_response[start_pos:end_pos+1]
        json_object = json.loads(json_string)

        domain.business_json = json_object

        domain.business_name    = domain.business_json['business_name']
        domain.naics_6          = domain.business_json['naics_6']

        for brand in domain.business_json['company_brands']:
            add_brand = Brand(brand=brand, domain=domain, type='brand')
            add_brand.save()

        for brand in domain.business_json['company_products']:
            add_brand = Brand(brand=brand, domain=domain, type='product')
            add_brand.save()

        for comp_domain in domain.business_json['competitor_domains']:
            try:
                comp_domain = comp_domain.replace('www.', '')
                comp_domain = comp_domain.replace('http://', '')
                comp_domain = comp_domain.replace('https://', '')

                try:
                    competitor = Domain.objects.get(domain=comp_domain)
                except:
                    if bool(re.fullmatch("([a-zA-Z]+[.][a-zA-Z]+)", comp_domain)):
                        print(f"Couldn't find matching competitor domain: {comp_domain} attempting to add domain.")
                        try:
                            new_domain = Domain(domain=comp_domain)
                            new_domain.save()
                            competitor = new_domain
                        except:
                            print(f"Couldn't create new domain for {new_domain}")
                    else:
                        print(f"Couldn't find matching competitor domain: {comp_domain} - this doesn't look like a valid domain, skipping import.")
                domain.competitors.add(competitor)
            except:
                print(f"Couldn't find matching competitor domain: {comp_domain} for source domain: {domain.domain}")
        
        domain.save()
    except:
        print("Couldn't save business json.")