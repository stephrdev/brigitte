from django.contrib import admin
from brigitte.repositories.models import Repository

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'user')

admin.site.register(Repository, RepositoryAdmin)

