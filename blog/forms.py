from django import forms

from blog.models import Comment


class EmailPostForm(forms.Form):
    """
    Email Post Form
    """

    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)


class CommentForm(forms.ModelForm):
    """
    Comments Model Form
    """

    class Meta:
        model = Comment
        fields = ("name", "email", "body")
