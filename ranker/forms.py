from django import forms
from .models import KeywordFile, TemplateItem, Message, Template, Project, Domain, Conversation
from django.forms import ModelForm, Form, ValidationError
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

class AddUserToProjectForm(Form):
    email = forms.EmailField()

    def clean_email(self): #Format is clean_<field_name>
        email = self.cleaned_data['email']

        try:
           User.objects.get(email=email)
        except:
           raise ValidationError('Email does not exist')

        # Remember to always return the cleaned data.
        return email

