from django import template
from django.template import RequestContext
from django.urls import reverse

register = template.Library()

menu = {
    'Главная': reverse('index'),
    'Каталог': reverse('store:category_list'),
    'Услуги': reverse('services:index'),
    'О нас': '#'
}


@register.inclusion_tag('components/header2.html', takes_context=True)
def include_menu(context: RequestContext):
    location = context['request'].path
    return {'request': context, 'menu': menu, 'location': location}
