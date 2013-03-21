# -*- coding: utf-8 -*-
from django import forms
from django.forms.models import modelformset_factory
from django.template.defaultfilters import slugify

from brigitte.repositories.models import Repository, RepositoryUser


class RepositoryDeleteForm(forms.Form):
    statisfied = forms.BooleanField('I want to delete this repository!')


class RepositoryForm(forms.ModelForm):
    class Meta:
        model = Repository
        exclude = ('user', 'slug', 'last_commit_date')

    def __init__(self, user, *args, **kwargs):
        super(RepositoryForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        slug = slugify(self.cleaned_data.get('title', ''))

        instance_pk = 0
        if self.instance:
            instance_pk = self.instance.pk

        if Repository.objects.filter(
            user=self.user,
            slug=slug
        ).exclude(
            pk=instance_pk
        ).count() > 0:
            raise forms.ValidationError('Repository name already in use.')

        return self.cleaned_data


RepositoryUserFormSet = modelformset_factory(
    RepositoryUser,
    extra=0,
    exclude=('repo', 'user'),
    can_delete=True
)
