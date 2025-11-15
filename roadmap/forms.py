from django import forms
from .models import Roadmap, Milestone, RoadmapVideo

class RoadmapForm(forms.ModelForm):
    class Meta:
        model = Roadmap
        fields = ['title', 'description', 'channel', 'level', 'estimated_hours', 'thumbnail', 'tags', 'is_featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'tags': forms.TextInput(attrs={'placeholder': 'python, django, web-development'}),
        }

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'order', 'estimated_hours', 'is_optional']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class RoadmapVideoForm(forms.ModelForm):
    class Meta:
        model = RoadmapVideo
        fields = ['video', 'order', 'is_required']
