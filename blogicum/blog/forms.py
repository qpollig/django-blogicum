from django import forms
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from .models import Category, Comments, Location, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        fields = '__all__'


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ('text', )
        widgets = {'text': forms.Textarea(attrs={'class': 'form-control'})}