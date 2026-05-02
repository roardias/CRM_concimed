from django import forms
from django.contrib.auth.models import User

from .models import UserProfile


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=UserProfile.Role.choices)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password"]
