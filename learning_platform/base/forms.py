"""
Forms personnalisés avec widgets date natifs HTML5
"""
from django import forms
from .models import Course, Module, Resource, Evaluation, Question


class DateInput(forms.DateInput):
    """Widget pour afficher un date picker HTML5"""
    input_type = 'date'


class CourseForm(forms.ModelForm):
    """Formulaire pour créer/modifier un cours"""
    class Meta:
        model = Course
        fields = ['title', 'description', 'estimated_duration', 'level', 'start_date', 'end_date', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Titre du cours'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'rows': 4,
                'placeholder': 'Description du cours'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Durée en heures'
            }),
            'level': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'start_date': DateInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'end_date': DateInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
        }


class ModuleForm(forms.ModelForm):
    """Formulaire pour créer/modifier un module"""
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Titre du module'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'rows': 4,
                'placeholder': 'Description du module'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Ordre d\'affichage'
            }),
        }


class ResourceForm(forms.ModelForm):
    """Formulaire pour créer/modifier une ressource"""
    class Meta:
        model = Resource
        fields = ['title', 'resource_type', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Titre de la ressource'
            }),
            'resource_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
        }


class EvaluationForm(forms.ModelForm):
    """Formulaire pour créer/modifier une évaluation"""
    class Meta:
        model = Evaluation
        fields = ['title', 'description', 'evaluation_type', 'deadline', 'max_score', 'passing_score', 'allow_retake', 'max_attempts', 'show_correct_answers', 'time_limit_minutes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Titre de l\'évaluation'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'rows': 3,
                'placeholder': 'Description (optionnel)'
            }),
            'evaluation_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'deadline': DateInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': '100'
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': '60'
            }),
            'allow_retake': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 bg-gray-800 border-gray-600 rounded focus:ring-blue-400'
            }),
            'max_attempts': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': '1'
            }),
            'show_correct_answers': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 bg-gray-800 border-gray-600 rounded focus:ring-blue-400'
            }),
            'time_limit_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Temps limite en minutes (optionnel)'
            }),
        }


class QuestionForm(forms.ModelForm):
    """Formulaire pour créer/modifier une question"""
    class Meta:
        model = Question
        fields = ['text', 'option1', 'option2', 'option3', 'option4', 'correct_option', 'points']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'rows': 3,
                'placeholder': 'Énoncé de la question'
            }),
            'option1': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Option A'
            }),
            'option2': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Option B'
            }),
            'option3': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Option C'
            }),
            'option4': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': 'Option D'
            }),
            'correct_option': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'placeholder': '1',
                'step': '0.5'
            }),
        }
