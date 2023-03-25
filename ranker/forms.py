from django import forms
from .models import KeywordFile, ProductTemplate
from django.forms import ModelForm

class KeywordFileForm(forms.ModelForm):
    class Meta:
        model = KeywordFile
        fields = ('filepath',)

class ProductTemplateForm(ModelForm):
    class Meta:
        model = ProductTemplate
        fields = ['prompt1', 'token1', 'prompt2', 'title', 'order', 'visible']
