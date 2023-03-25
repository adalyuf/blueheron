from django import forms
from .models import KeywordFile, ProductTemplate, Message, Product
from django.forms import ModelForm

class KeywordFileForm(forms.ModelForm):
    class Meta:
        model = KeywordFile
        fields = ('filepath',)

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['product', 'scope']

class ProductTemplateForm(ModelForm):
    class Meta:
        model = ProductTemplate
        fields = ['prompt1', 'token1', 'prompt2']

class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = ['prompt']
