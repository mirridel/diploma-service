# myapp/forms.py
from dal import autocomplete
from django import forms

from . import models


class CarForm(forms.ModelForm):
    vendor = autocomplete.SelectMultiple(url='services:car-autocomplete'),

    class Meta:
        model = models.Car
        fields = ('vendor',)


class ServiceBookingForm(forms.ModelForm):
    class Meta:
        model = models.ServiceRecord
        fields = ['car', 'notes']
        widgets = {'booking_date': None,
                   'car': autocomplete.ListSelect2(url='services:car-autocomplete',
                                                   attrs={'class': 'form-control', 'style': 'width: 100%;'}),
                   'notes': forms.Textarea(attrs={'cols': 15, 'rows': 3})}
