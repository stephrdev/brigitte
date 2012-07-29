# -*- coding: utf-8 -*-
import struct, base64

from django import forms
from django.utils.translation import ugettext_lazy as _

from userprofiles.forms import RegistrationForm

from brigitte.accounts.models import Profile, SshPublicKey


class ProfileRegistrationForm(RegistrationForm):
    short_info = forms.CharField(widget=forms.Textarea, required=False)

    def save_profile(self, new_user, *args, **kwargs):
        Profile.objects.create(
            user=new_user,
            short_info=self.cleaned_data['short_info']
        )

class SshPublicKeyForm(forms.ModelForm):
    class Meta:
        model = SshPublicKey
        exclude = ('user',)

    def clean_key(self):
        try:
            key = self.cleaned_data['key']
            ktype, key_string, comment = key.split()
            data = base64.decodestring(key_string)
            int_len = 4
            str_len = struct.unpack('>I', data[:int_len])[0]

            if data[int_len:int_len+str_len] == ktype:
                return key
        except:
            pass

        raise forms.ValidationError(
            _(u'The provided key is not valid. Please supply a valid key.'))
