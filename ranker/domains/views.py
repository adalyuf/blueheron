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

import csv
import os
import openai
import markdown
import json

class DomainListView(generic.ListView):
    model = Domain
    queryset = Domain.objects.filter(adult_content__exact=False).order_by('rank')
    
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = KTLayout.init(context) # A function to init the global layout. It is defined in _keenthemes/__init__.py file
        KTTheme.addVendors(['amcharts', 'amcharts-maps', 'amcharts-stock']) # Include vendors and javascript files for dashboard widgets
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
    keyword_files = domain.keywordfile_set.all()
    conversations = domain.conversation_set.all()
    ai_models = AIModel.objects.all()
    templates = Template.objects.filter(scope__exact='per_domain').filter(project__isnull=True)
    notice = ''
    if request.method == 'POST':
        form = KeywordFileForm(request.POST, request.FILES)
        if form.is_valid():
            instance = KeywordFile(filepath=request.FILES['filepath'], domain_id = domain.id)
            instance.save()
            notice = "File uploaded successfully."
    else:
        form = KeywordFileForm()
    return render(request, 'ranker/domain_detail.html', {'domain': domain, 'keyword_files': keyword_files, 'form': form, 'notice': notice, 'conversations': conversations, 'templates': templates, 'ai_models': ai_models })

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