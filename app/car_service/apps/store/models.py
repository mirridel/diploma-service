import uuid

from django.contrib.admin import display
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from mptt.models import MPTTModel, TreeForeignKey
from photologue.models import Photo
from slugify import slugify

from car_service.apps.customuser.models import User


class Category(MPTTModel):
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, null=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children',
                            verbose_name='Родитель')

    class MPTTMeta:
        order_insertion_by = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class ProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(visibility=True)


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    price = models.PositiveIntegerField(default=0, verbose_name='Цена')
    visibility = models.BooleanField(default=True, verbose_name='Видимость')
    images = models.ManyToManyField(Photo, blank=True, related_name='images', verbose_name='Изображения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    is_discount = models.BooleanField(default=False, verbose_name='Скидка')

    objects = models.Manager()
    filtered_objects = ProductManager()

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self, *args, **kwargs):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class ProductSpecs(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    value = models.CharField(max_length=255, verbose_name='Значение')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, verbose_name='Товар')

    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'

    def __str__(self):
        return f'{self.name}'


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    is_discount = models.BooleanField(default=False, verbose_name='Скидка')

    class Meta:
        verbose_name = 'Состав'
        verbose_name_plural = 'Состав'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_item_summary(self):
        return self.quantity * self.price


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Пользователь')
    cart = models.ManyToManyField(CartItem, related_name='items', verbose_name='Корзина')
    summary = models.PositiveIntegerField(blank=True, null=True, verbose_name="Итог")
    zip = models.CharField(max_length=6, verbose_name='Индекс', default='')
    city = models.CharField(max_length=255, verbose_name='Город', default='Новосибирск')
    address = models.CharField(max_length=255, verbose_name='Адрес', default='')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Заказ #{self.id}"

    def get_summary(self):
        summary = 0
        items = self.cart.all()
        for item in items:
            summary += item.get_item_summary()
        return summary

    def save(self, *args, **kwargs):
        if not self.summary:
            self.summary = self.get_summary()
        super().save(*args, **kwargs)

    def get_total_quantity(self):
        quantity = 0
        items = self.cart.values_list('quantity', flat=True)
        for item in items:
            quantity += item
        return quantity

    @property
    @display(description='Состав корзины')
    def display_cart(self):
        q = self.cart.all()
        content = ''.join(
            [f'<a href="{item.product.get_absolute_url()}"><div>{item.quantity} x {item.product.name}</div></a>' for
             item in q])
        return mark_safe(content)
