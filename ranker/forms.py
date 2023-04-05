from django import forms
from .models import KeywordFile, TemplateItem, Message, Template, Project, Domain, Conversation
from django.forms import ModelForm, Form
from accounts.models import User

class KeywordFileForm(forms.ModelForm):
    class Meta:
        model = KeywordFile
        fields = ('filepath',)

class TemplateForm(ModelForm):
    class Meta:
        model = Template
        fields = ['template', 'scope']

class TemplateItemForm(ModelForm):
    class Meta:
        model = TemplateItem
        fields = ['prompt1', 'token1', 'prompt2']

class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = ['prompt']

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['project']

class AddDomainToProjectForm(ModelForm):
    class Meta:
        model = Domain
        fields = ['domain']

class CreateConversationsForm(Form):
    class Meta:
        model = Conversation
        fields = ['template', 'ai_model']

class AddUserToProjectForm(ModelForm):
    class Meta:
        model = User
        fields = ['email']

