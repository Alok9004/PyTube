from django import forms
from .models import Roadmap, RoadmapChannel

class RoadmapForm(forms.ModelForm):
    class Meta:
        model = Roadmap
        fields = ['title', 'description', 'difficulty', 'estimated_hours', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Roadmap title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe this learning path...'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RoadmapChannelForm(forms.ModelForm):
    class Meta:
        model = RoadmapChannel
        fields = ['channel', 'order']
        widgets = {
            'channel': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

