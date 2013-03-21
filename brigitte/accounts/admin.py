# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from brigitte.accounts.models import Profile, SshPublicKey


admin.site.unregister(User)


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 1
    max_num = 1


class SshPublicKeyInline(admin.TabularInline):
    model = SshPublicKey
    extra = 1


class UserProfileAdmin(UserAdmin):
    inlines = [ProfileInline, SshPublicKeyInline]

admin.site.register(User, UserProfileAdmin)
