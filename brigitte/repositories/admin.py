from django.contrib import admin
from brigitte.repositories.models import Repository

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'path')

admin.site.register(Repository, RepositoryAdmin)

