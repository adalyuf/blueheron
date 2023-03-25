from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils import timezone, html
from django.core.paginator import (Paginator, EmptyPage,PageNotAnInteger,)

from .models import Domain, KeywordFile, Conversation, Product, ProductTemplate, Message
from .forms import KeywordFileForm, ProductTemplateForm, MessageForm, ProductForm

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

def domain_detail(request, domain_id):
    domain = get_object_or_404(Domain, pk=domain_id)
    keyword_files = domain.keywordfile_set.all()
    conversations = domain.conversation_set.all()
    products = Product.objects.filter(scope__exact='per_domain')
    notice = ''
    if request.method == 'POST':
        form = KeywordFileForm(request.POST, request.FILES)
        if form.is_valid():
            instance = KeywordFile(filepath=request.FILES['filepath'], domain_id = domain.id)
            instance.save()
            notice = "File uploaded successfully."
    else:
        form = KeywordFileForm()
    return render(request, 'ranker/domain_detail.html', {'domain': domain, 'keyword_files': keyword_files, 'form': form, 'notice': notice, 'conversations': conversations, 'products': products})

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

def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    messages = conversation.message_set.filter(visible=True).order_by('order')
    if request.method == 'POST':
        openai.api_key = os.getenv("OPENAI_API_KEY")
        message_array = [{"role": "system", "content": "You are a helpful assistant."}]
        for message in messages:
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
    
    default_page = 1
    page_number = request.GET.get('page', default_page)

    # Paginate items
    items_per_page = 1
    paginator = Paginator(messages, items_per_page)

    try:
        items = paginator.get_page(page_number)
    except PageNotAnInteger:
        items = paginator.get_page(default_page)
    except EmptyPage:
        items = paginator.get_page(paginator.num_pages)

    return render(request, 'ranker/conversation_detail.html', {'conversation': conversation, 'messages': messages, 'items': items})

def conversation_add(request, product_id, domain_id):
    product = get_object_or_404(Product, pk=product_id)
    domain = get_object_or_404(Domain, pk=domain_id)
    if Conversation.objects.filter(product_id__exact=product.id).filter(domain_id__exact=domain.id).count() == 0:
        conversation = Conversation(domain=domain, product=product)
        conversation.save()
        templates = product.producttemplate_set.all()
        for template in templates:
            m = Message(
                prompt = template.prompt1, #TODO: Add logic that uses tokens and concatenates with other parts of prompt
                title = template.title,
                visible = template.visible,
                order = template.order,
                conversation = conversation
            )
            m.prompt = m.prompt.replace("@currentDomain", conversation.domain.domain)
            m.save()
    else:
        conversation = Conversation.objects.filter(product_id__exact=product.id).filter(domain_id__exact=domain.id).first()
        #TODO: Add combined unique requirement on conversation(product, domain) and figure out how to do this better
    return redirect('conversation_edit', conversation_id=conversation.id)


def conversation_edit(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    messages = conversation.message_set.all().order_by('order')
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = MessageForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.order = 100
            message.save()

    # if a GET (or any other method) we'll create a blank form
    else:
        form = MessageForm()
    return render(request, 'ranker/conversation_edit.html', {'messages': messages, 'conversation': conversation, 'form': form})

def conversation_update_order(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    messages = conversation.message_set.all().order_by('order')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        message_ids = json.loads(request.body) 
        print(message_ids)
        index = 0
        while index < len(message_ids):
            message = get_object_or_404(Message, pk=int(message_ids[index]))
            message.order = index
            message.save()
            index += 1

    form = MessageForm()

    return render(request, 'ranker/conversation_edit.html', {'conversation': conversation, 'messages': messages, 'form': form})

def product_list(request):
    products = Product.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = ProductForm
    return render(request, 'ranker/product_list.html', {'products': products, 'form': form})

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product_templates = product.producttemplate_set.all().order_by('order')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ProductTemplateForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            template = form.save(commit=False)
            template.product = product
            template.order = 100
            template.save()

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ProductTemplateForm()

    return render(request, 'ranker/product_detail.html', {'product':product, 'product_templates':product_templates, 'form': form})

def product_template_order(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product_templates = product.producttemplate_set.all().order_by('order')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        product_template_ids = json.loads(request.body) 
        print(product_template_ids)
        index = 0
        while index < len(product_template_ids):
            pt = get_object_or_404(ProductTemplate, pk=int(product_template_ids[index]))
            pt.order = index
            pt.save()
            index += 1


    form = ProductTemplateForm()

    return render(request, 'ranker/product_detail.html', {'product':product, 'product_templates':product_templates, 'form': form})