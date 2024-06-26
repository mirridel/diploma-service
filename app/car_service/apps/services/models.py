import datetime
import functools
from copy import deepcopy
from datetime import timedelta

from django.contrib.admin import display
from django.db import models
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now, get_current_timezone
from slugify import slugify

from car_service.apps.customuser.models import User


class Garage(models.Model):
    location = models.CharField(max_length=100, verbose_name='Местоположение')

    class Meta:
        verbose_name = 'Бокс'
        verbose_name_plural = 'Боксы'

    @property
    @display(description='Кол-во сотрудников')
    def display_staff_count(self):
        return self.staff.count()

    def __str__(self):
        return f'{self.location}'


class Staff(models.Model):
    firstname = models.CharField(max_length=100, verbose_name='Имя')
    lastname = models.CharField(max_length=100, verbose_name='Фамилия')
    position = models.CharField(max_length=100, verbose_name='Должность')
    garage = models.ForeignKey(Garage, on_delete=models.SET_NULL, blank=True, null=True, related_name='staff',
                               verbose_name='Место работы')

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return f'{self.firstname} {self.lastname} [{self.position}]'


class Car(models.Model):
    vendor = models.CharField(max_length=255, verbose_name='Производитель')
    model = models.CharField(max_length=255, verbose_name='Модель')

    class Meta:
        verbose_name = 'ТС'
        verbose_name_plural = 'ТС'

    def __str__(self):
        return f"{self.vendor} {self.model}"


class ServiceCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name='Категория')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, verbose_name='Категория')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    price = models.PositiveIntegerField(default=0, verbose_name='Цена')
    fixed_price = models.BooleanField(default=False, verbose_name='Фикс. цена?')

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ServiceRecord(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Клиент')
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Автомобиль')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Услуга')
    date = models.DateTimeField(verbose_name='Дата записи')
    notes = models.TextField(blank=True, null=True, verbose_name='Примечание')

    class Meta:
        verbose_name = 'Запись на услугу'
        verbose_name_plural = 'Записи на услугу'

    def __str__(self):
        return f'{self.client.first_name} ({self.client.phone_number}) - {self.service.name} ({self.date.astimezone(tz=get_current_timezone()).strftime("%d.%m.%Y %H:%M")}) '


class ServiceExecution(models.Model):
    service_record = models.OneToOneField(ServiceRecord, on_delete=models.CASCADE, verbose_name='Запись')
    garage = models.ForeignKey(Garage, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Бокс')
    start_time = models.DateTimeField(blank=True, null=True, verbose_name='Время начала')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name='Время окончания')
    conclusion = models.TextField(blank=True, null=True, default=None, verbose_name='Заключение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время обновления', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'В обработке'),
        ('confirmed', 'Подтвержден'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ], default='scheduled', verbose_name='Статус')

    @property
    @display(description='Запись на услугу')
    def display_record(self):
        rec = self.service_record
        ref = reverse('admin:%s_%s_change' % ('services', 'servicerecord'), args=[self.service_record.id])
        content = f'''
        <a href='{ref}'>
            <table>
                <tbody>
                    <tr>
                        <td>Имя</td>
                        <td>{rec.client.first_name}</td>
                    </tr>
                    <tr>
                        <td>Тел.</td>
                        <td>{rec.client.phone_number}</td>
                    </tr>
                    <tr>
                        <td>ТС</td>
                        <td>{rec.car}</td>
                    </tr>
                    <tr>
                        <td>Услуга</td>
                        <td>{rec.service}</td>
                    </tr>
                    <tr>
                        <td>Время</td>
                        <td>{rec.date.astimezone(tz=get_current_timezone()).strftime("%d.%m.%Y %H:%M")}</td>
                    </tr>
                </tbody>
            </table>
        </a>
        '''
        return mark_safe(content)

    def __str__(self):
        return f'Запись о выполнении #{self.id}'

    class Meta:
        verbose_name = 'Запись об исполнении'
        verbose_name_plural = 'Записи об исполнении'


def lru_cache(maxsize=128, typed=False, copy=False):
    if not copy:
        return functools.lru_cache(maxsize, typed)

    def decorator(f):
        cached_func = functools.lru_cache(maxsize, typed)(f)

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return deepcopy(cached_func(*args, **kwargs))

        return wrapper

    return decorator


@lru_cache(copy=True)
def get_slots(current_date, range_date, start_time, end_time):
    dates = [current_date + timedelta(days=x) for x in range(range_date)]
    times = [datetime.time(hour=x) for x in range(start_time, end_time)]
    slots = {date: list(times) for date in dates}
    return slots


def get_free_slots(current_date, d=7):
    now = current_date.date()
    total_garages = Garage.objects.count()
    q = ServiceRecord.objects.filter(date__date__range=(now, now + timedelta(days=d))).annotate(
        count_records=Count('id')).values_list('date__date',
                                               'date__time',
                                               'count_records')
    free_slots = get_slots(now, d, 8, 22)
    for date, time, total_count in q:
        if total_count == total_garages:
            free_slots[date].remove(time)
    return free_slots
