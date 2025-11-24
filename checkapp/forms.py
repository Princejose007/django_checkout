from django import forms
from .models import BillingDetails


class BillingDetailsForm(forms.ModelForm):
    class Meta:
        model = BillingDetails
        fields = ['phone_number', 'Full_name', 'Address']
