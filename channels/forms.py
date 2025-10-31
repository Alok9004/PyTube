from django import forms
from .models import Channel

class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description', 'banner_image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Channel name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Channel description'}),
        }
