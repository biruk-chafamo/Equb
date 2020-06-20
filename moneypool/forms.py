from django import forms
from .models import *


class CreateEqubForm(forms.ModelForm):
    class Meta:
        model = Equb
        fields = ['name', 'value', 'capacity', 'cycle']

#
# class CreateClientForm(forms.ModelForm):
#     class Meta:
#         model = Client
#         fields = ['user', 'bank_account']
