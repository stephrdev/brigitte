from django.contrib import admin

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from brigitte.accounts.models import Profile
from brigitte.accounts.models import EmailVerification, RegistrationProfile

admin.site.unregister(User)

class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 1
    max_num = 1

class UserProfileAdmin(UserAdmin):
    inlines = [ProfileInline,]

admin.site.register(User, UserProfileAdmin)

class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'old_email', 'new_email', 'expiration_date',
                    'is_approved', 'is_expired')
    list_filter = ('is_approved', 'is_expired')

admin.site.register(EmailVerification, EmailVerificationAdmin)

class RegistrationProfileAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'activation_key_expired')
    search_fields = ('user__username', 'user__first_name')

admin.site.register(RegistrationProfile, RegistrationProfileAdmin)

