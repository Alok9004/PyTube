from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        help_texts={
            'username':None
            }
        widgets = {
            'username':forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'email':forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'password':forms.PasswordInput(attrs={'placeholder': 'Enter your password'})
        }
        labels = { 
            'username':'',
            'email':'',
            'password':''
        }

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        label='',
        widget=forms.TextInput(attrs={'placeholder':'Enter Username'})
    )
    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder':'Enter password'})
    )
    

class ForgotPasswordForm(forms.Form):
    username = forms.CharField(
        max_length=100, 
        label='',
        widget=forms.TextInput(attrs={'placeholder':'Enter Username'})
        )
    new_password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder':'New password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder':'confirm password'}), 
        label=''
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

    
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError("No user found with this username.")

        if new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data