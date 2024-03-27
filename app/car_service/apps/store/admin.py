from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from mptt.admin import DraggableMPTTAdmin

from car_service.apps.store import models
from car_service.apps.store.models import Product


class CategoryAdmin(DraggableMPTTAdmin):
    search_fields = ['name']


admin.site.register(models.Category, CategoryAdmin)


class SpecInline(admin.StackedInline):
    model = models.ProductSpecs


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    list_display = ('name', 'price', 'description')  # Отображаемые поля в списке
    search_fields = ('name',)  # Поля для поиска
    list_filter = ('category',)  # Фильтры
    # Другие настройки админ-панели

    # Дополнительные настройки для импорта
    list_import = ('csv', 'xlsx')  # Разрешенные форматы файлов для импорта
    import_id_fields = ('name',)  # Поля, используемые для идентификации объектов при импорте

    inlines = [SpecInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["queryset"] = models.Category.objects.filter(children__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(models.ProductSpecs)


@admin.register(models.CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'quantity', 'price',)  # Отображаемые поля в списке
    search_fields = ()  # Поля для поиска


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at', 'summary', 'display_cart')  # Отображаемые поля в списке
    readonly_fields = ('display_cart',)
    search_fields = ('user__email',)  # Поля для поиска
    list_filter = ('created_at', 'updated_at', 'status')  # Фильтры
    ordering = ('-created_at', '-updated_at',)

