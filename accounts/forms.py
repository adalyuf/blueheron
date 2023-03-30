from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from accounts.models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ( 'email', 'first_name', 'last_name',  'password1', 'password2', )

class LoginForm(AuthenticationForm):
    email = forms.EmailField(max_length=254, help_text='Please enter your email address.')


    class Meta:
        model = User
        fields = ('email', 'password1')