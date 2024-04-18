import time

import pymorphy2
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect

from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from yoomoney import Quickpay

from . import forms, models
from .forms import CheckoutForm
from .models import Category, Product
from .services import CartHandler
from ..customuser.forms import ClientForm
from ..customuser.models import User
from ... import settings


def category_list(request):
    categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'store/category_list.html', {'categories': categories})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    category_path = category.get_ancestors(include_self=False)
    children = category.get_children()
    products = Product.filtered_objects.filter(category=category) if not children else None
    return render(request, 'store/category_detail.html',
                  {'category': category, 'children': children, 'products': products, 'category_path': category_path})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    category_path = product.category.get_ancestors(include_self=True)
    user_cart = CartHandler(request)
    is_added = str(product.id) in user_cart.cart.keys()
    return render(request, 'store/product_detail.html',
                  context={'product': product, 'category_path': category_path, 'is_added': is_added})


def get_total_content(d):
    c = sum(d.values())
    morph = pymorphy2.MorphAnalyzer()
    w = morph.parse('товар')[0].make_agree_with_number(c).word
    s = sum(product.price * quantity for product, quantity in d.items())
    return c, w, s


def cart(request):
    user_cart = CartHandler(request)
    products = Product.filtered_objects.filter(id__in=user_cart.cart.keys())

    cookie = None
    if len(user_cart) != products.count():
        q = products.values_list('id', flat=True)
        user_cart.fix(q)
        cookie = user_cart.save()

    d = {product: user_cart.cart[str(product.id)] for product in products}
    c, w, s = get_total_content(d)

    response = render(request, 'store/cart_detail.html', context={'d': d, 'c': f'{c} {w}', 's': s})
    if cookie:
        response = response.set_cookie('cart', cookie)
    return response


def cart_api(request):
    if request.method != 'GET':
        return http.HttpResponseBadRequest()
    command = request.GET.get('command')
    if command not in ('create', 'read', 'update', 'delete'):
        return http.HttpResponseBadRequest()
    pk = request.GET.get('pk')

    user_cart = CartHandler(request)
    if command == 'create':
        user_cart.add(pk, 1)
    elif command == 'update':
        action = request.GET.get('action')
        user_cart.update(pk, action, 1)
    elif command == 'delete':
        user_cart.remove(pk)
    cookie = user_cart.save()
    response = http.JsonResponse({'user_cart': user_cart.__str__()})
    response.set_cookie('cart', cookie)
    return response


@login_required
def checkout_view(request):
    user_cart = CartHandler(request)
    products = Product.filtered_objects.filter(id__in=user_cart.cart.keys())
    if len(user_cart) != products.count():
        q = products.values_list('id', flat=True)
        user_cart.fix(q)
    d = {product: user_cart.cart[str(product.id)] for product in products}
    c, w, s = get_total_content(d)
    if request.method == 'POST':
        client_form = ClientForm(request.POST)
        form = forms.OrderForm(request.POST)
        if client_form.is_valid() and form.is_valid():
            u = User.objects.get(id=request.user.id)
            u.first_name = client_form.cleaned_data['first_name']
            u.last_name = client_form.cleaned_data['last_name']
            u.phone_number = client_form.cleaned_data['phone_number']
            u.save()
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            for p, q in d.items():
                item = models.CartItem.objects.create(product=p, quantity=q, price=p.price)
                order.cart.add(item)
            order.save()
            if settings.YOOMONEY_PAYMENT:
                quick_pay = Quickpay(
                    receiver=settings.YOOMONEY_RECEIVER,
                    quickpay_form="shop",
                    targets='Заказ №{}'.format(order.id),
                    paymentType="SB",
                    successURL=reverse('me'),
                    sum=order.summary,
                    label='{}'.format(order.id)
                )
                return redirect(quick_pay.redirected_url)
            messages.success(request, 'Вы успешно оформили заказ!')
            return redirect('me')
    else:
        client_form = ClientForm()
        client_form.fields['first_name'].initial = request.user.first_name
        client_form.fields['last_name'].initial = request.user.last_name
        client_form.fields['phone_number'].initial = request.user.phone_number
        form = forms.OrderForm()
    return render(request, 'store/checkout.html',
                  context={'client_form': client_form, 'form': form, 'd': d, 'c': f'{c} {w}', 's': s})
