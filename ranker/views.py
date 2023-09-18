from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
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
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import F, Max
from django.db import transaction

from .models import Domain, KeywordFile, Conversation, Template, TemplateItem, Message, Project, ProjectUser, ProjectDomain, AIModel, Keyword, Brand, Statistic, add_value, Sitemap
from .forms import KeywordFileForm, TemplateItemForm, MessageForm, TemplateForm, AddDomainToProjectForm, CreateConversationsForm

import csv
import os
import openai
import markdown
import json
import redis 

import logging

logger = logging.getLogger(__name__)
broker = redis.Redis(host=os.getenv("REDIS_HOST"), port=6379, db=0, password=os.getenv("REDIS_PASS"))
backend  = redis.Redis(host=os.getenv("REDIS_HOST"), port=6379, db=1, password=os.getenv("REDIS_PASS"))

def sitemap(request):
    context = {}
    context['sitemap_index'] = Sitemap.objects.all().exclude(category__exact='static')
    return render(request, 'ranker/sitemap_index.xml', context, content_type='application/xml' )

def sitemap_static(request):
    context = {}
    context['sitemap_static'] = Sitemap.objects.filter(category__exact='static')
    return render(request, 'ranker/sitemap_static.xml', context, content_type='application/xml' )

def sitemap_redirect(request, folder, category, page_num):
    return redirect(f"https://topranks-media-public.s3.us-east-2.amazonaws.com/media/sitemaps/{folder}/sitemap-{category}-{page_num}.xml")

class TemplateListView(generic.ListView):
    model = Template
    queryset = Template.objects.filter(project__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = KTLayout.init(context) # A function to init the global layout. It is defined in _keenthemes/__init__.py file
        KTTheme.addVendors(['amcharts', 'amcharts-maps', 'amcharts-stock']) # Include vendors and javascript files for dashboard widgets    
        context['form'] = TemplateForm()
        return context

class KeywordListView(generic.ListView):
    model = Keyword
    queryset = Keyword.objects.filter(answered_at__isnull=False).order_by('-answered_at')[:500]
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = KTLayout.init(context) # A function to init the global layout. It is defined in _keenthemes/__init__.py file
        context['keywords_total']       = Statistic.objects.get(key="keywords_total").value
        context['keywords_available']   = Statistic.objects.get(key="keywords_available").value
        context['keywords_pending']     = Statistic.objects.get(key="keywords_pending").value
        context['keywords_answered']    = Statistic.objects.get(key="keywords_answered").value
        context['broker_size'] = broker.llen('celery')
        context['backend_size'] = backend.dbsize()
        if os.getenv("ENVIRONMENT") == "production":
            context['kw_batch_size'] = 10000
        else:
            context['kw_batch_size'] = 100
        return context

def keyword_search(request):
    user_search = request.GET['user_search']
    if user_search:
        search_query = SearchQuery(user_search, search_type="websearch")
        queryset = Keyword.objects.annotate(rank=SearchRank(F("search_vector"), search_query)).filter(search_vector=search_query).order_by("-rank")[:100]
    else:
        queryset = Keyword.objects.filter(answered_at__isnull=False) 
    return render(request, 'ranker/keyword_list.html', {'keyword_list': queryset, 'kw_batch_size': 10000})

def reset_keyword_queue(request):
    pending_keywords = Keyword.objects.filter(answered_at__isnull=True).filter(requested_at__isnull=False)
    # Add pending keywords back to keywords available to be queued stat
    add_value('keywords_available', pending_keywords.count())

    # Reset pending keywords stat to 0 (can't use add_value helper because we're setting to 0 instead of adding)
    with transaction.atomic():
        stat = Statistic.objects.select_for_update().get(key='keywords_pending')
        stat.value = 0
        stat.save()
    # Flush Redis cache and results
    broker.flushdb()
    backend.flushdb()
    # Unset each individual keywords requested at value
    item_list= []
    for keyword in pending_keywords:
        keyword.requested_at = None
        item_list.append(keyword)
    Keyword.objects.bulk_update(item_list, ["requested_at"], batch_size=10000)
    return redirect('keyword_list')

class KeywordDetailView(generic.DetailView):
    model = Keyword

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        related_keywords = []
        for query in self.get_object().likely_next_queries:
            search_query = SearchQuery(query, search_type="websearch")
            related_kws = Keyword.objects.annotate(rank=SearchRank(F("search_vector"), search_query)).filter(search_vector=search_query).order_by("-rank")[:3]
            for kw in related_kws:
                related_keywords.append(kw)
        context['related_keywords'] = related_keywords
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.request.path != self.object.get_absolute_url():
            return redirect(self.object, permanent=True)

        return super().get(self, request, args, kwargs)



def autocomplete_brands(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        brands = Brand.objects.all().filter(brand__icontains=term)
        return JsonResponse(list(brands.values()), safe=False)
    return render(request, 'index.html')

def keyword_gap(request, brand1_id=None, brand2_id=None):
    context = {}
    
    if request.method == 'POST':
        if brand1_id:
            brand1 = get_object_or_404(Brand, id = brand1_id)
        else:
            brand1 = get_object_or_404(Brand, id = request.POST['brand1'])
        if brand2_id:
            brand2 = get_object_or_404(Brand, id = brand2_id)
        else:
            brand2 = get_object_or_404(Brand, id = request.POST['brand2'])
        context['brand1'] = brand1 
        context['brand2'] = brand2
        search_query = SearchQuery(f"{brand1.brand} OR {brand2.brand}", search_type="websearch")
        context['keyword_list'] = Keyword.objects.annotate(rank=SearchRank(F("search_vector"), search_query)).annotate(traffic=(Max('keywordposition__search_volume'))).filter(search_vector=search_query).exclude(ai_answer__isnull=True).order_by("-traffic")[:100]
    return render(request, 'ranker/keyword_gap.html', context)



def template_create(request, project_id=None):
    template_form = TemplateForm()
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            if project_id:
                project = get_object_or_404(Project, id=project_id)
                template.project = project
            template.save()
            return redirect('template_detail', template.id)
    return redirect('template_list')

def template_create_conversations(request):
    if request.method == 'POST':
        template = get_object_or_404(Template, id = request.POST['template_id'])
        ai_model = get_object_or_404(AIModel, id = request.POST['ai_model_id'])
        project = template.project
        domains = project.domain.all()
        for domain in domains:
            try:
                conversation = Conversation.objects.get(domain=domain, template=template, ai_model=ai_model, project=project)
                conversation.message_set.all().delete() #TODO: confirm that we actually want to delete all existing messages when rebuilding conversations from a template
            except:
                conversation = Conversation(domain=domain, template=template, ai_model=ai_model, project=project)
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
    return redirect('project_detail', project.id)    

    # How this generic view works:
    # Calls the template at .templates/<app>/<model>_list.html (templates/ranker/template_list.html)
    # Passes the object <model>_list (template_list)
    # queryset = Template.objects.all()
    # context = {'context_object_name': queryset}

    # Below are examples of how to override the defaults for generic list views
    # context_object_name = 'book_list'   # your own name for the list as a template variable
    # queryset = Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war
    # template_name = 'books/my_arbitrary_template_name_list.html'  # Specify your own template name/location


class GetTemplateView(View):

    def get(self, request, *args, **kwargs):
        view = TemplateDetailView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = TemplateDetailFormView.as_view()
        return view(request, *args, **kwargs)

class TemplateDetailView(generic.DetailView):
    model = Template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = KTLayout.init(context) # A function to init the global layout. It is defined in _keenthemes/__init__.py file
        template = self.get_object()
        context['ai_model_list'] = AIModel.objects.all()
        if template.project:
            self.request.session['template'] = template.id
            self.request.session['project'] = template.project.id
            domain_array = []
            domains = template.project.domain.all()
            for domain in domains:
                domain_array.append(domain.id)
            self.request.session['domains'] = domain_array
            context['create_conversations_form'] = CreateConversationsForm()
        context['form'] = TemplateItemForm()
        return context

class TemplateDetailFormView(SingleObjectMixin, FormView):
    template_name = 'ranker/template_detail.html'
    form_class = TemplateItemForm #We display the template item form
    model = Template #But look up things by the template class

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        template = self.get_object()
        form = self.get_form()
        if form.is_valid():
            template_item = form.save(commit=False)
            template_item.template = template
            template_item.order = 100
            template_item.save()
        return self.form_valid(form)

    def get_success_url(self):
        return reverse('template_detail', kwargs={'pk': self.object.pk})

@login_required
def template_delete(request, template_id):
    template = get_object_or_404(Template, pk=template_id)

    if request.method == 'POST':
        if template.project:
            project = template.project
            template.delete()
            return redirect('project_settings', project.id)
    template.delete()
    
    return redirect('template_list')

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
    
    return redirect('template_detail', template.id)

class DashboardsView(TemplateView):
    template_name = 'pages/dashboards/index.html'

    # Predefined function
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # A function to init the global layout. It is defined in _keenthemes/__init__.py file
        context = KTLayout.init(context)

        # Include vendors and javascript files for dashboard widgets
        KTTheme.addVendors(['amcharts', 'amcharts-maps', 'amcharts-stock'])

        return context


