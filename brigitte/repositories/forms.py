from django import forms
from django.forms.models import modelformset_factory

from brigitte.repositories.models import Repository, RepositoryUser

class RepositoryForm(forms.ModelForm):
    class Meta:
        model = Repository
        exclude = ('user', 'slug')

RepositoryUserFormSet = modelformset_factory(
    RepositoryUser,
    extra=0,
    exclude=('repo', 'user'),
    can_delete=True
)
