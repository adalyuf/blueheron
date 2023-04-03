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

from .models import Domain, KeywordFile, Conversation, Template, TemplateItem, Message, Project, ProjectUser, ProjectDomain, AIModel
from .forms import KeywordFileForm, TemplateItemForm, MessageForm, TemplateForm, AddDomainToProjectForm

import csv
import os
import openai
import markdown
import json

class TemplateListView(generic.ListView):
    model = Template
    queryset = Template.objects.filter(project__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = KTLayout.init(context) # A function to init the global layout. It is defined in _keenthemes/__init__.py file
        KTTheme.addVendors(['amcharts', 'amcharts-maps', 'amcharts-stock']) # Include vendors and javascript files for dashboard widgets    
        context['form'] = TemplateForm()
        return context

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
        KTTheme.addVendors(['amcharts', 'amcharts-maps', 'amcharts-stock']) # Include vendors and javascript files for dashboard widgets

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
    
    return redirect('template_detail', template_id=template.id)

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

class ProjectListView(generic.ListView):
    model = Project

    def get_queryset(self):
        user = self.request.user
        projects = user.project_set.all()
        return projects
    
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    global_template_list = Template.objects.filter(scope__exact='per_domain').filter(project__isnull=True)
    project_template_list = project.template_set.all()
    project_domain_list = project.domain.all()
    global_domain_list = Domain.objects.all()
    template_form = TemplateForm()
    domain_form = AddDomainToProjectForm()
    context = {}
    context['project'] = project
    context['global_template_list'] = global_template_list
    context['project_template_list'] = project_template_list
    context['project_domain_list'] = project_domain_list
    context['global_domain_list'] = global_domain_list
    context['template_form'] = template_form
    context['domain_form'] = domain_form
    return render(request, 'ranker/project_detail.html', context)

def project_add_domain(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    domain_id = request.POST['domain']
    domain = get_object_or_404(Domain, pk=domain_id)
    project.domain.add(domain)
    return redirect('project_detail', project.id)

def project_remove_domain(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    domain_id = request.POST['domain']
    domain = get_object_or_404(Domain, pk=domain_id)
    project.domain.remove(domain)
    return redirect('project_detail', project.id)

class ProjectCreate(CreateView):
    model = Project
    fields = ['project']
    
    def form_valid(self, form):
        project = form.save()
        user = self.request.user
        project.user.add(user)
        return super().form_valid(form)

class ProjectUpdate(UpdateView):
    model = Project
    fields = ['project']

class ProjectDelete(DeleteView):
    model = Project
    success_url = reverse_lazy('project_list')
