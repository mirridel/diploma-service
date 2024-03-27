import hashlib
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Value, CharField, Sum, F
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

from car_service import settings
from car_service.apps.services.models import ServiceExecution, ServiceRecord
from car_service.apps.store.models import Order


def index(request):
    return render(request, 'index.html', context={})


def me(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    service_records = ServiceExecution.objects.filter(service_record__client=request.user).order_by(
        '-service_record__date')
    return render(request, 'me.html', {'orders': orders, 'service_records': service_records})


@staff_member_required
def statistics(request):
    n = now().date()
    l = (n - timedelta(days=15)).strftime('%Y-%m-%d')
    r = (n + timedelta(days=15)).strftime('%Y-%m-%d')

    return render(request, 'statistics.html',
                  context={'n': n, 'l': l, 'r': r, 'order_status_choices': Order.STATUS_CHOICES})


checkbox_dict = {
    'service_category_name': 'service__category__name',
    'service_name': 'service__name',
    'car': 'car_concat',
    'date': 'd',
}


def service_statistics(request):
    n = now()
    l = request.GET.get('l', n.date())
    r = request.GET.get('r', n.date() + timedelta(days=30))
    g = request.GET.getlist('g')

    sub_array = []
    for key, item in checkbox_dict.items():
        if key in g:
            sub_array.append(item)
    data = ServiceRecord.objects.filter(date__range=(l, r))
    if 'car' in g:
        data = data.annotate(car_concat=Concat('car__vendor', Value(' '), 'car__model', output_field=CharField()))
    if 'date' in g:
        data = data.annotate(d=F('date__date'))
    data = data.values(*sub_array).annotate(c=Count('id'), s=Sum('service__price'))

    context = {'fields': sub_array, 'data': data}
    return context


def income_statistics(request):
    n = now()
    l = request.GET.get('l', n.date())
    r = request.GET.get('r', n.date() + timedelta(days=30))
    s = request.GET.get('s', None)
    t = request.GET.get('t', 'created_at')
    data = Order.objects.filter(created_at__range=(l, r))
    if s:
        data = data.filter(status=s)
    count = data.aggregate(Count('id'))['id__count']
    summ = data.aggregate(Sum('summary'))['summary__sum']
    if t == 'created_at':
        data = data.annotate(date=F('created_at__date'))
    else:
        data = data.annotate(date=F('updated_at__date'))
    data = data.values('date').annotate(s=Sum('summary'), c=Count('id'))
    context = {'data': data, 'count': count, 'summ': summ}
    return context


@staff_member_required
def get_statistics(request, string):
    if string == 'income':
        context = income_statistics(request)
        return render(request, 'statistics/income_statistics.html', context)
    elif string == 'service':
        context = service_statistics(request)
        return render(request, 'statistics/service_statistics.html', context)
    return HttpResponse('None')


@csrf_exempt
def success(request):
    notification_type = request.POST.get('notification_type', None)
    operation_id = request.POST.get('operation_id', None)
    amount = request.POST.get('amount', None)
    currency = request.POST.get('currency', None)
    datetime = request.POST.get('datetime', None)
    sender = request.POST.get('sender', None)
    codepro = request.POST.get('codepro', None)
    verification_code = settings.YOOMONEY_VERIFICATION_CODE
    label = request.POST.get('label', None)
    sha1_hash = request.POST.get('sha1_hash', None)

    confirmation_string = f'{notification_type}&{operation_id}&{amount}&{currency}&{datetime}&{sender}&{codepro}&{verification_code}&{label}'

    try:
        byte_string = str.encode(confirmation_string)
        hash_object = hashlib.sha1(byte_string)
        hex_dig = hash_object.hexdigest()
        # Проверка на подлинность запроса
        if sha1_hash and hex_dig == sha1_hash and label:
            order = get_object_or_404(Order, pk=label)
            order.status = 'processing'
            order.save()
        else:

            raise Exception("PAYMENT VERIFICATION ERROR!")
    except Exception as ex:
        print(ex)

    return HttpResponse(status=200)
