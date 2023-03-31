from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils import timezone, html
from django.core.paginator import (Paginator, EmptyPage,PageNotAnInteger,)
from django.core.management import call_command
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib import messages as djmessages
from _keenthemes.__init__ import KTLayout
from _keenthemes.libs.theme import KTTheme

from .models import Domain, KeywordFile, Conversation, Template, TemplateItem, Message
from .forms import KeywordFileForm, TemplateItemForm, MessageForm, TemplateForm

import csv
import os
import openai
import markdown
import json

def domain_list(request):
    default_page = 1
    page_number = request.GET.get('page', default_page)
    # Get queryset of items to paginate
    domain_list = Domain.objects.filter(adult_content__exact=False).order_by('rank')

    # Paginate items
    items_per_page = 100
    paginator = Paginator(domain_list, items_per_page)

    try:
        items = paginator.get_page(page_number)
    except PageNotAnInteger:
        items = paginator.get_page(default_page)
    except EmptyPage:
        items = paginator.get_page(paginator.num_pages)

    context = { 'items': items}
    return render(request, 'ranker/domain_list.html', context)

@login_required
def domain_detail(request, domain_id):
    domain = get_object_or_404(Domain, pk=domain_id)
    keyword_files = domain.keywordfile_set.all()
    conversations = domain.conversation_set.all()
    templates = Template.objects.filter(scope__exact='per_domain')
    notice = ''
    if request.method == 'POST':
        form = KeywordFileForm(request.POST, request.FILES)
        if form.is_valid():
            instance = KeywordFile(filepath=request.FILES['filepath'], domain_id = domain.id)
            instance.save()
            notice = "File uploaded successfully."
    else:
        form = KeywordFileForm()
    return render(request, 'ranker/domain_detail.html', {'domain': domain, 'keyword_files': keyword_files, 'form': form, 'notice': notice, 'conversations': conversations, 'templates': templates})

@login_required
def keywordfile_make_primary(request, domain_id, keywordfile_id):
    domain = get_object_or_404(Domain, pk=domain_id)
    keywordfile = get_object_or_404(KeywordFile, pk=keywordfile_id)
    files = domain.keywordfile_set.filter(primary=True)
    for f in files:
        f.primary = False
        f.save()
    keywordfile.primary = True 
    keywordfile.save()
    return redirect('domain_detail', domain_id=domain_id)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    chat_messages = conversation.message_set.filter(visible=True).order_by('order')
    if request.method == 'POST':
        openai.api_key = os.getenv("OPENAI_API_KEY")
        message_array = [{"role": "system", "content": "You are a helpful assistant."}]
        for message in chat_messages:
            message_array.append({"role": "user", "content": message.prompt})
            o = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=message_array,
                temperature=0.6,
            )
            message.response = o['choices'][0]['message']['content']
            message_array.append({"role": "assistant", "content": message.response})
            message.formatted_response = html.format_html(markdown.markdown(message.response, extensions=['tables']))
            message.save()
        djmessages.success(request, "Messages retrieved.")
    
    default_page = 1
    page_number = request.GET.get('page', default_page)

    # Paginate items
    items_per_page = 1
    paginator = Paginator(chat_messages, items_per_page)

    try:
        items = paginator.get_page(page_number)
    except PageNotAnInteger:
        items = paginator.get_page(default_page)
    except EmptyPage:
        items = paginator.get_page(paginator.num_pages)
    return render(request, 'ranker/conversation_detail.html', {'conversation': conversation, 'chat_messages': chat_messages, 'items': items})

@login_required
def conversation_add(request, template_id, domain_id):
    template = get_object_or_404(Template, pk=template_id)
    domain = get_object_or_404(Domain, pk=domain_id)
    if Conversation.objects.filter(template_id__exact=template.id).filter(domain_id__exact=domain.id).count() == 0:
        conversation = Conversation(domain=domain, template=template)
        conversation.save()
        template_items = template.templateitem_set.all()
        for template_item in template_items:
            m = Message(
                prompt = template_item.prompt1, #TODO: Add logic that uses tokens and concatenates with other parts of prompt
                title = template_item.title,
                visible = template_item.visible,
                order = template_item.order,
                conversation = conversation
            )
            m.prompt = m.prompt.replace("@currentDomain", conversation.domain.domain)
            m.save()
    else:
        conversation = Conversation.objects.filter(template_id__exact=template.id).filter(domain_id__exact=domain.id).first()
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
        call_command('mpresponses', '--conversation', conversation.id)

    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def message_delete(request, message_id):
    message = get_object_or_404(Message, pk=message_id)
    conversation = message.conversation

    if request.method == 'POST':
        message.delete()
        djmessages.error(request, "Message deleted.")
    
    return redirect('conversation_edit', conversation_id=conversation.id)

@login_required
def template_list(request):
    templates = Template.objects.all()
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = TemplateForm
    return render(request, 'ranker/template_list.html', {'templates': templates, 'form': form})

@login_required
def template_detail(request, template_id):
    template = get_object_or_404(Template, pk=template_id)
    template_items = template.templateitem_set.all().order_by('order')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = TemplateItemForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            template_item = form.save(commit=False)
            template_item.template = template
            template_item.order = 100
            template_item.save()

    # if a GET (or any other method) we'll create a blank form
    else:
        form = TemplateItemForm()

    return render(request, 'ranker/template_detail.html', {'template':template, 'template_items':template_items, 'form': form})

@login_required
def template_item_order(request, template_id):
    template = get_object_or_404(Template, pk=template_id)
    template_items = template.templateitem_set.all().order_by('order')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        template_item_ids = json.loads(request.body) 
        index = 0
        while index < len(template_item_ids):
            pt = get_object_or_404(TemplateItem, pk=int(template_item_ids[index]))
            pt.order = index
            pt.save()
            index += 1
    form = TemplateItemForm()

    return render(request, 'ranker/template_detail.html', {'template':template, 'template_items':template_items, 'form': form})

@login_required
def template_item_delete(request, TemplateItem_id):
    template_item = get_object_or_404(TemplateItem, pk=TemplateItem_id)
    template = template_item.template

    if request.method == 'POST':
        template_item.delete()
    
    return redirect('template_detail', template_id=template.id)

class DashboardsView(TemplateView):
    # Default template file
    # Refer to dashboards/urls.py file for more pages and template files
    template_name = 'pages/dashboards/index.html'


    # Predefined function
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        """
        # Example to get page name. Refer to dashboards/urls.py file.
        url_name = resolve(self.request.path_info).url_name

        if url_name == 'dashboard-2':
            # Example to override settings at the runtime
            settings.KT_THEME_DIRECTION = 'rtl'
        else:
            settings.KT_THEME_DIRECTION = 'ltr'
        """

        # A function to init the global layout. It is defined in _keenthemes/__init__.py file
        context = KTLayout.init(context)

        # Include vendors and javascript files for dashboard widgets
        KTTheme.addVendors(['amcharts', 'amcharts-maps', 'amcharts-stock'])

        return context