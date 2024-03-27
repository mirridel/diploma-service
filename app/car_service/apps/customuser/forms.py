from django import forms

from car_service.apps.customuser import models


class ClientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(ClientForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['phone_number'].required = True

    class Meta:
        model = models.User
        fields = ['first_name', 'last_name', 'phone_number']
        widgets = {'phone_number': forms.TextInput(attrs={'type': 'tel'}), }
