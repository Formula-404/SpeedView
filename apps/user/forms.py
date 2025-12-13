from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.html import escape
import re
from .models import UserProfile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm Password'

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email = escape(email.strip())
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        username = escape(username.strip())
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError("Username can only contain letters, numbers, and @/./+/-/_ characters")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        return username

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        return escape(username.strip())

class EditProfileForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(EditProfileForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        username = escape(username.strip())
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError("Username can only contain letters, numbers, and @/./+/-/_ characters")
        if User.objects.filter(username=username).exclude(id=self.user.id).exists():
            raise forms.ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email = escape(email.strip())
        if User.objects.filter(email=email).exclude(id=self.user.id).exists():
            raise forms.ValidationError("Email already exists")
        return email

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Current Password")
    new_password1 = forms.CharField(widget=forms.PasswordInput, required=True, label="New Password",
                                     help_text="Password must be at least 8 characters")
    new_password2 = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm New Password")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Current password is incorrect")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("New passwords do not match")
            if len(new_password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters")

        return cleaned_data

class DeleteAccountForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, required=True,
                               label="Confirm Password",
                               help_text="Enter your password to confirm account deletion")
    confirm_text = forms.CharField(max_length=50, required=True,
                                   label="Type 'DELETE' to confirm",
                                   help_text="Type DELETE in capital letters")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(DeleteAccountForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError("Password is incorrect")
        return password

    def clean_confirm_text(self):
        confirm_text = self.cleaned_data.get('confirm_text')
        if confirm_text != 'DELETE':
            raise forms.ValidationError("You must type 'DELETE' exactly to confirm")
        return confirm_text
