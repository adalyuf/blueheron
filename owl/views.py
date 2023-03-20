from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils import timezone, html
from django.core.paginator import (Paginator, EmptyPage,PageNotAnInteger,)

from .models import Domain, KeywordFile, Conversation
from .forms import KeywordFileForm

import csv
import os
import openai
import markdown 

def domain_list(request):
    default_page = 1
    page_number = request.GET.get('page', default_page)

    # Get queryset of items to paginate
    domain_list = Domain.objects.order_by('rank')

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
    return render(request, 'owl/domain_list.html', context)

def domain_detail(request, domain_id):
    domain = get_object_or_404(Domain, pk=domain_id)
    keyword_files = domain.keywordfile_set.all()
    conversations = domain.conversation_set.all()
    notice = ''
    if request.method == 'POST':
        form = KeywordFileForm(request.POST, request.FILES)
        if form.is_valid():
            instance = KeywordFile(filepath=request.FILES['filepath'], domain_id = domain.id)
            instance.save()
            notice = "File uploaded successfully."
    else:
        form = KeywordFileForm()
    return render(request, 'owl/domain_detail.html', {'domain': domain, 'keyword_files': keyword_files, 'form': form, 'notice': notice, 'conversations': conversations})

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
    messages = get_object_or_404(Conversation, pk=conversation_id).message_set.filter(visible=True).order_by('order')
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

    return render(request, 'owl/conversation_detail.html', {'messages': messages, 'items': items})