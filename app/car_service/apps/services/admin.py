from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from car_service.apps.services import models


@admin.register(models.Car)
class CarAdmin(ImportExportModelAdmin):
    list_display = ('vendor', 'model')  # Отображаемые поля в списке
    search_fields = ('vendor', 'model')  # Поля для поиска

    # Дополнительные настройки для импорта
    list_import = ('csv', 'xlsx')  # Разрешенные форматы файлов для импорта
    import_id_fields = ('vendor', 'model')  # Поля, используемые для идентификации объектов при импорте


class StaffInline(admin.StackedInline):
    model = models.Staff
    extra = 1


@admin.register(models.Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('id', 'firstname', 'lastname', 'position', 'garage')  # Отображаемые поля в списке
    search_fields = ()  # Поля для поиска
    list_filter = ('garage',)
    # Другие настройки админ-панели


@admin.register(models.Garage)
class GarageAdmin(admin.ModelAdmin):
    list_display = ('id', 'location', 'display_staff_count')  # Отображаемые поля в списке
    search_fields = ()  # Поля для поиска
    list_filter = ()
    inlines = [StaffInline]
    # Другие настройки админ-панели


admin.site.register(models.ServiceCategory)


@admin.register(models.Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name', 'price', 'fixed_price')  # Отображаемые поля в списке
    search_fields = ('name',)  # Поля для поиска
    # Другие настройки админ-панели


@admin.register(models.ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'car', 'service', 'date')  # Отображаемые поля в списке
    search_fields = ('service__name',)  # Поля для поиска
    # Другие настройки админ-панели


@admin.register(models.ServiceExecution)
class ServiceExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'display_record', 'garage', 'start_time', 'end_time', 'status')  # Отображаемые поля в списке
    search_fields = ()  # Поля для поиска
    list_filter = ('created_at', 'updated_at', 'status',)
    # Другие настройки админ-панели
