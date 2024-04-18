import datetime
from datetime import timedelta

from dal import autocomplete
from django.contrib import messages
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django.views import generic

from car_service.apps.customuser.forms import ClientForm
from car_service.apps.customuser.models import User
from car_service.apps.services import models, forms
from car_service.apps.services.models import get_free_slots


class ServiceList(generic.ListView):
    model = models.Service
    context_object_name = 'services'
    template_name = 'services/index.html'
    ordering = ('category__name',)


@login_required
def booking(request, slug=None):
    service = get_object_or_404(models.Service, slug=slug)
    now = timezone.now()
    free_slots = get_free_slots(now)
    if request.method == 'POST':
        ds = request.POST.get('btnradio')
        form_client = ClientForm(request.POST)
        form = forms.ServiceBookingForm(request.POST)
        if form.is_valid() and form_client.is_valid() and ds:
            u = User.objects.get(id=request.user.id)
            u.first_name = form_client.cleaned_data['first_name']
            u.last_name = form_client.cleaned_data['last_name']
            u.phone_number = form_client.cleaned_data['phone_number']
            u.save()

            booking_service = form.save(commit=False)
            datetime_str = request.POST.get('btnradio')
            date = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            booking_service.date = date
            booking_service.client = request.user
            booking_service.service = service
            booking_service.save()
            models.ServiceExecution.objects.create(service_record=booking_service)

            messages.success(request, 'Вы успешно оформили запись!')
            return redirect('me')
        if not ds:
            messages.error(request, 'Выберите дату и время для записи')
    else:
        form_client = ClientForm()
        form_client.fields['first_name'].initial = request.user.first_name
        form_client.fields['last_name'].initial = request.user.last_name
        form_client.fields['phone_number'].initial = request.user.phone_number
        form = forms.ServiceBookingForm()
    return render(request, 'services/booking.html',
                  context={'free_slots': free_slots, 'service': service, 'form_client': form_client, 'form': form})


class CarAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return models.Car.objects.none()
        qs = models.Car.objects.all()
        if self.q:
            qs = qs.annotate(car_concat=Concat('vendor', Value(' '), 'model')).filter(Q(car_concat__icontains=self.q))
        return qs
