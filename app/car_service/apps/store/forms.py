from django import forms

from car_service.apps.store import models


class OrderForm(forms.ModelForm):
    class Meta:
        model = models.Order
        fields = '__all__'
        exclude = ('user', 'cart', 'summary', 'status')


class CheckoutForm(forms.Form):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    zip = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        # здесь можно добавить дополнительные проверки
        return cleaned_data
