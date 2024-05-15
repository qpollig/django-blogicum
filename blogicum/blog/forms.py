from django import forms
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from .models import Category, Comment, Location, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        fields = '__all__'


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
