from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ranker.models import Domain, TokenType, Token, Template, TemplateItem, Conversation, Message, AIModel

import csv

class Command(BaseCommand):
    help = "build all conversations from existing templates and template items"

    def add_arguments(self, parser):
        parser.add_argument('--template', action='store', type=int)
        parser.add_argument('--ai_model', action='store', type=int)

    def handle(self, *args, **options):

        # For each TemplateItem
        # Determine if scope is global or per_domain
        # If per_domain, go through every domain and:
        # Create a conversation with template and domain foreign keys
        # Create a message for each template_item
        # Special handling for domain attributes:
        # replace @currentDomain with domain.domain
        try:
            template = Template.objects.get(id = options['template'])
            ai_model = AIModel.objects.get(id = options['ai_model'])
            print(f"Template: {template}")
            print(f"AI Model: {ai_model}")
        except:
            print("Command needs both --template and --ai_model flags to be passed")

        start_time = timezone.now()

        domains = Domain.objects.filter(adult_content__exact=False).order_by('rank')

        #Create one conversation for every domain
        conversations = []
        for domain in domains:
            c = Conversation(domain=domain, template=template, ai_model=ai_model)
            conversations.append(c)
            if len(conversations) > 5000:
                Conversation.objects.bulk_create(conversations, ignore_conflicts=True)
                self.stdout.write(f"Bulk upload completed: {len(conversations)} conversations")
                conversations = []
        if conversations:
            Conversation.objects.bulk_create(conversations, ignore_conflicts=True)
            self.stdout.write(f"Bulk upload completed: {len(conversations)} conversations")
        
        #Create a message for every conversation based on its associated templateset
        template_items = template.templateitem_set.all()
        conversations = template.conversation_set.all()
        messages = []
        for conversation in conversations:
            for template_item in template_items:
                m = Message(
                    prompt  = template_item.prompt1, #TODO: Add logic that uses tokens and concatenates with other parts of prompt
                    title   = template_item.title,
                    visible = template_item.visible,
                    order   = template_item.order,
                    conversation    = conversation,
                    template_item   = template_item,
                )
                m.prompt = m.prompt.replace("@currentDomain", conversation.domain.domain)
                messages.append(m)
                if len(messages) > 5000:
                    Message.objects.bulk_create(messages)
                    self.stdout.write(f"Bulk upload completed: {len(messages)} messages")
                    messages = []
        if messages:
            Message.objects.bulk_create(messages)
            self.stdout.write(f"Bulk upload completed: {len(messages)} messages")

        end_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f"Building conversations took: {(end_time-start_time).total_seconds()} seconds."
            )
        )

        # notes on performance improvements, 100 domains, 1 template, 13 template_items (1300 messages)
        # using save() on each, and nested for loops, 8.9 seconds
        # splitting into a loop for conversations and a loop for messages (still using save()): 8.8 seconds
        # doing a bulk save for 5000 at a time: 0.09 seconds!!
