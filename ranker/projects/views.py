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
from ranker.forms import KeywordFileForm, TemplateItemForm, MessageForm, TemplateForm, AddDomainToProjectForm, AddUserToProjectForm, CreateConversationsForm
from accounts.models import User
from ranker.tasks import save_message_response, call_openai

import csv
import os
import openai
import markdown
import json

class ProjectListView(generic.ListView):
    model = Project

    def get_queryset(self):
        user = self.request.user
        projects = user.project_set.all()
        return projects
    
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    context = {}
    context['project'] = project
    context['project_template_list']= project.template_set.all()
    context['project_domain_list']  = project.domain.all().order_by('domain')
    context['conversation_list']    = Conversation.objects.filter(project=project)
    context['project_user_list']    = project.user.all()
    context['ai_model_list']        = AIModel.objects.all()
    context['create_conversations_form'] = CreateConversationsForm()
    return render(request, 'ranker/project_detail.html', context)

def project_settings(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    context = {}
    context['project'] = project
    context['project_template_list']= project.template_set.all()
    context['project_domain_list']  = project.domain.all().order_by('domain')
    context['project_user_list']    = project.user.all()
    context['global_domain_list']   = Domain.objects.filter(adult_content=False)
    context['template_form']        = TemplateForm()
    context['domain_form']          = AddDomainToProjectForm()
    context['user_form']            = AddUserToProjectForm()
    return render(request, 'ranker/project_settings.html', context)

def project_add_domain(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    domain_id = request.POST['domain']
    domain = get_object_or_404(Domain, pk=domain_id)
    project.domain.add(domain)
    return redirect('project_settings', project.id)

def project_remove_domain(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    domain_id = request.POST['domain']
    domain = get_object_or_404(Domain, pk=domain_id)
    project.domain.remove(domain)
    return redirect('project_settings', project.id)

def project_add_user(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    email = request.POST['email']
    user = get_object_or_404(User, email=email)
    project.user.add(user)
    return redirect('project_settings', project.id)

def project_remove_user(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    user_id = request.POST['user']
    user = get_object_or_404(User, pk=user_id)
    project.user.remove(user)
    return redirect('project_settings', project.id)

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

@login_required
def project_get_all_responses(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        djmessages.info(request, "Requesting responses.")
        for conversation in project.conversation_set.all():
            for message in conversation.message_set.all():
                message.requested_at = timezone.now()
                message.save()
                call_openai.apply_async( (message.prompt,), link=save_message_response.s(message.id)) #note the comma in arguments, critical to imply tuple, otherwise thinks array
    return redirect('conversation_detail', conversation_id=conversation.id)