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

from ranker.models import Domain, KeywordFile, Conversation, Template, TemplateItem, Message, Project, ProjectUser, ProjectDomain, AIModel, Keyword
from ranker.forms import KeywordFileForm, TemplateItemForm, MessageForm, TemplateForm
from ranker.tasks import call_openai, save_keyword_response, save_business_json

import csv
import os
import openai
import markdown
import json

class DomainListView(generic.ListView):
    model = Domain
    queryset = Domain.objects.filter(adult_content__exact=False).filter(keywordfile__primary=None).order_by('rank')
    
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = KTLayout.init(context) # A function to init the global layout. It is defined in _keenthemes/__init__.py file
        KTTheme.addVendors(['amcharts', 'amcharts-maps', 'amcharts-stock']) # Include vendors and javascript files for dashboard widgets
        context['domain_count'] = Domain.objects.count()
        context['domain_not_adult'] = Domain.objects.filter(adult_content__exact=False).count()
        context['domain_na_missing_busdata'] = Domain.objects.filter(adult_content__exact=False).filter(business_json__isnull=True).count()
        context['domain_na_with_busdata'] = Domain.objects.filter(adult_content__exact=False).filter(business_json__isnull=False).count()
        return context

def domain_search(request):
    user_search = request.GET['user_search']
    if user_search:
        queryset = Domain.objects.filter(adult_content__exact=False).filter(domain__icontains=user_search).order_by('rank')
    else:
        queryset = Domain.objects.filter(adult_content__exact=False).order_by('rank')
    return render(request, 'ranker/domain_list.html', {'domain_list': queryset})

@login_required
def domain_detail(request, domain_id):
    domain = get_object_or_404(Domain, pk=domain_id)
    context = {}
    context['domain'] = domain
    context['keyword_files'] = domain.keywordfile_set.all()
    context['conversations'] = domain.conversation_set.all()
    context['ai_models'] = AIModel.objects.all()
    context['templates'] = Template.objects.filter(scope__exact='per_domain').filter(project__isnull=True)
    context['brands'] = domain.brand_set.all().order_by('type', 'brand')
    notice = ''
    if request.method == 'POST':
        form = KeywordFileForm(request.POST, request.FILES)
        if form.is_valid():
            instance = KeywordFile(filepath=request.FILES['filepath'], domain_id = domain.id)
            instance.save()
            notice = "File uploaded successfully."
    else:
        form = KeywordFileForm()
    context['form'] = form
    context['notice'] = notice
    return render(request, 'ranker/domain_detail.html', context)

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
    call_command('importkeywords', kwfile=keywordfile.id)
    djmessages.success(request, 'Keywords loaded')
    return redirect('domain_detail', domain_id=domain_id)

@login_required
def get_keyword_responses(request):
    if os.getenv("ENVIRONMENT") == "production":
        kw_batch_size = 10000
    else:
        kw_batch_size = 100
    
    keyword_list = Keyword.objects.filter(requested_at=None)[:kw_batch_size]

    item_list = []
    for keyword in keyword_list:
        keyword.requested_at = timezone.now()
        item_list.append(keyword)
    Keyword.objects.bulk_update(item_list, ["requested_at"], batch_size=5000)

    #Request responses for each keyword
    for keyword in keyword_list:
        prompt = "If a user searches for @currentKeyword, what is their user intent, how would you rephrase this as a natural language question, please provide a thorough and detailed answer to the natural language question, what was their likely previous query, and what could be their next query? Provide your response as a simple JSON object, with keys \"user_intent\", \"natural_language_question\", \"ai_answer\", \"likely_previous_queries\", and \"likely_next_queries\". If this is likely to be their first or last query in their journey, answer \"none\" in the field"
        prompt = prompt.replace("@currentKeyword", keyword.keyword)
        call_openai.apply_async( (prompt,), link=save_keyword_response.s(keyword.id)) #note the comma in arguments, critical to imply tuple, otherwise thinks array, passes response as first argument

    return redirect('keyword_list')

def get_business_data(request):
    if os.getenv("ENVIRONMENT") == "production":
        batch_size = 10000
    else:
        batch_size = 100

    domain_list = Domain.objects.filter(adult_content__exact=False).filter(business_json__isnull=True).filter(business_attempts__exact=0).order_by('rank')[:batch_size]
    for domain in domain_list:
        domain.business_attempts = domain.business_attempts + 1
        domain.business_retrieved_at = timezone.now()
        domain.save()
        prompt = f"For {domain.domain}, provide their Business Name, 6-digit NAICS code, Brands, Domains of Competitors, Products in a simple JSON object. In your response, use \"business_name\", \"naics_6\", \"company_brands\", \"competitor_domains\", and \"company_products\" as keys in the JSON."
        call_openai.apply_async( (prompt,), link=save_business_json.s(domain.id))
    
    djmessages.success(request, f'Getting business data for {batch_size} domains')
    return redirect('domain_list')
