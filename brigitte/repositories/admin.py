# -*- coding: utf-8 -*-
from django.contrib import admin

from brigitte.repositories.models import (Repository, RepositoryUser,
    RepositoryUpdate)


class RepositoryUserInline(admin.TabularInline):
    model = RepositoryUser
    extra = 2

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'user')
    inlines = [RepositoryUserInline,]

admin.site.register(Repository, RepositoryAdmin)

class RepositoryUpdateAdmin(admin.ModelAdmin):
    list_display = ('updated', 'update', 'repo', 'user', 'is_exported',
        'exported')
    list_filter = ('updated', 'is_exported', 'exported', 'update')

admin.site.register(RepositoryUpdate, RepositoryUpdateAdmin)
