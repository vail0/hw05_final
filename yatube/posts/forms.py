from django import forms
from django.forms import TextInput

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'текст',
            'group': 'группа',
            'image': 'картинка',
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'текст',
        }
        widgets = {
            'text': TextInput(
                attrs={'class': 'form-control',
                       'placeholder': 'Введите текст комментария',
                       }),
        }
