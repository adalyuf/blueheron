from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils import timezone, html
from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger,)
from django.core.management import call_command
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib import messages as djmessages
from django.views import generic, View
from django.urls import reverse, reverse_lazy
from _keenthemes.__init__ import KTLayout
from _keenthemes.libs.theme import KTTheme

from ranker.models import Domain, KeywordFile, Conversation, Template, TemplateItem, Message, Project, ProjectUser, ProjectDomain, AIModel
from ranker.forms import KeywordFileForm, TemplateItemForm, MessageForm, TemplateForm
from ranker.tasks import save_message_response, call_openai
from celery import chain

import csv
import os
import openai
import markdown
import json


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    chat_messages = conversation.message_set.filter(visible=True).order_by('order')
    
    default_page = 1
    page_number = request.GET.get('page', default_page)

    # Paginate items
    items_per_page = 1
    paginator = Paginator(chat_messages, items_per_page)

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(default_page)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    return render(request, 'ranker/conversation_detail.html', {'conversation': conversation, 'chat_messages': chat_messages, 'page_obj': page_obj})

@login_required
def conversation_add(request, template_id, domain_id, ai_model_id):
    template = get_object_or_404(Template, pk=template_id)
    domain = get_object_or_404(Domain, pk=domain_id)
    ai_model = get_object_or_404(AIModel, pk=ai_model_id)
    if Conversation.objects.filter(template_id__exact=template.id).filter(domain_id__exact=domain.id).filter(ai_model_id__exact=ai_model.id).filter(project_id__isnull=True).count() == 0:
        conversation = Conversation(domain=domain, template=template, ai_model=ai_model)
        conversation.save()
        template_items = template.templateitem_set.all()
        for template_item in template_items:
            m = Message(
                prompt      = template_item.prompt1, #TODO: Add logic that uses tokens and concatenates with other parts of prompt
                title       = template_item.title,
                visible     = template_item.visible,
                order       = template_item.order,
                conversation = conversation,
                template_item = template_item,
            )
            m.prompt = m.prompt.replace("@currentDomain", conversation.domain.domain)
            m.save()
    else:
        conversation = Conversation.objects.get(template=template, domain=domain, ai_model=ai_model, project=None)
        #TODO: Add combined unique requirement on conversation(template, domain) and figure out how to do this better
    return redirect('conversation_edit', conversation_id=conversation.id)

@login_required
def conversation_edit(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    chat_messages = conversation.message_set.all().order_by('order')
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = MessageForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.order = 100
            message.save()
            djmessages.success(request, "Message updated.")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = MessageForm()
    return render(request, 'ranker/conversation_edit.html', {'chat_messages': chat_messages, 'conversation': conversation, 'form': form})

@login_required
def conversation_update_order(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    chat_messages = conversation.message_set.all().order_by('order')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        message_ids = json.loads(request.body) 
        index = 0
        while index < len(message_ids):
            message = get_object_or_404(Message, pk=int(message_ids[index]))
            message.order = index
            message.save()
            index += 1

    form = MessageForm()
    #Note that we are calling these "chat_messages" this is to namespace them from django 'messages' which we also want to use
    return render(request, 'ranker/conversation_edit.html', {'conversation': conversation, 'chat_messages': chat_messages, 'form': form})

@login_required
def conversation_get_responses(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)

    if request.method == 'POST':
        djmessages.info(request, "Requesting responses.")
        for message in conversation.message_set.all():
            message.requested_at = timezone.now()
            message.save()
            call_openai.apply_async( (message.prompt,), link=save_message_response.s(message.id)) #note the comma in arguments, critical to imply tuple, otherwise thinks array
    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def message_delete(request, message_id):
    message = get_object_or_404(Message, pk=message_id)
    conversation = message.conversation

    if request.method == 'POST':
        message.delete()
        djmessages.error(request, "Message deleted.")
    
    return redirect('conversation_edit', conversation_id=conversation.id)