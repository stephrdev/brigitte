# -*- coding: utf-8 -*-
from django.contrib import admin

from brigitte.repositories.models import Repository, RepositoryUser


class RepositoryUserInline(admin.TabularInline):
    model = RepositoryUser
    extra = 2

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'user')
    inlines = [RepositoryUserInline,]

admin.site.register(Repository, RepositoryAdmin)
