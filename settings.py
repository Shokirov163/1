
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mailsystem_db',
        'USER': 'mailsystem_user',
        'PASSWORD': 'SecurePassword123!',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
База данных mailsystem_db создана командой PostgreSQL CREATE DATABASE mailsystem_db OWNER mailsystem_user;, пользователь mailsystem_user с паролем создан командой CREATE USER mailsystem_user WITH PASSWORD 'SecurePassword123!';, предоставлены права GRANT ALL PRIVILEGES ON DATABASE mailsystem_db TO mailsystem_user;.
Модели данных определены в файлах models.py каждого приложения. Модель Office (приложение core):
from django.db import models
class Office(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название офиса')
    code = models.CharField(max_length=10, unique=True, verbose_name='Код офиса')
    address = models.TextField(verbose_name='Адрес')
    responsible_person = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='responsible_for_offices', verbose_name='Ответственный')

    class Meta:
        verbose_name = 'Офис'
        verbose_name_plural = 'Офисы'
        ordering = ['name']

    def __str__(self):
        return self.name
Модель Employee:
class Employee(models.Model):
    personnel_number = models.CharField(max_length=20, unique=True, verbose_name='Табельный номер')
    full_name = models.CharField(max_length=200, verbose_name='ФИО')
    position = models.CharField(max_length=200, verbose_name='Должность')
    department = models.CharField(max_length=200, verbose_name='Подразделение')
    office = models.ForeignKey(Office, on_delete=models.PROTECT, verbose_name='Офис')
    phone = models.CharField(max_length=50, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['personnel_number'], name='idx_personnel_number'),
            models.Index(fields=['full_name'], name='idx_full_name'),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.position})"
Модель IncomingShipment (приложение shipments):
from django.db import models
from django.contrib.auth.models import User
from core.models import Employee, Office, ShipmentType
import datetime

class IncomingShipmentManager(models.Manager):
    def get_undelivered(self, office_id=None):
        queryset = self.filter(status__in=['Зарегистрировано', 'Ожидает получения'])
        if office_id:
            queryset = queryset.filter(office_id=office_id)
        return queryset

    def get_by_tracking_number(self, tracking_number):
        try:
            return self.get(tracking_number=tracking_number)
        except self.model.DoesNotExist:
            return None

class IncomingShipment(models.Model):
    STATUS_CHOICES = [
        ('Зарегистрировано', 'Зарегистрировано'),
        ('Ожидает получения', 'Ожидает получения'),
        ('Получено', 'Получено'),
        ('Возвращено', 'Возвращено'),
    ]

    tracking_number = models.CharField(max_length=50, unique=True, verbose_name='Идентификатор')
    received_date = models.DateField(verbose_name='Дата поступления')
    shipment_type = models.ForeignKey(ShipmentType, on_delete=models.PROTECT, verbose_name='Тип отправления')
    sender = models.CharField(max_length=200, verbose_name='Отправитель')
    recipient = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name='Получатель')
    office = models.ForeignKey(Office, on_delete=models.PROTECT, verbose_name='Офис назначения')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Зарегистрировано', verbose_name='Статус')
    notes = models.TextField(blank=True, verbose_name='Примечание')
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registered_shipments',
                                      verbose_name='Зарегистрировал')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='received_shipments', verbose_name='Получил')
    received_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата получения')
    notification_sent = models.BooleanField(default=False, verbose_name='Уведомление отправлено')

    objects = IncomingShipmentManager()

    class Meta:
        verbose_name = 'Входящее отправление'
        verbose_name_plural = 'Входящие отправления'
        ordering = ['-received_date', '-registered_at']
        indexes = [
            models.Index(fields=['tracking_number'], name='idx_tracking_number'),
            models.Index(fields=['received_date'], name='idx_received_date'),
            models.Index(fields=['office', 'status'], name='idx_office_status'),
            models.Index(fields=['recipient'], name='idx_recipient'),
        ]

    def generate_tracking_number(self):
        date_str = self.received_date.strftime('%Y%m%d')
        count = IncomingShipment.objects.filter(received_date=self.received_date).count()
        number = str(count + 1).zfill(4)
        return f"{date_str}-{number}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_number} - {self.recipient.full_name}"
Миграции базы данных созданы командой python manage.py makemigrations, применены командой python manage.py migrate. Django создал таблицы в PostgreSQL: core_office, core_employee, core_shipmenttype, core_courierservice, shipments_incomingshipment, shipments_outgoingshipment, auth_user (встроенная таблица пользователей), core_eventlog. Проверка структуры таблицы выполнена командой PostgreSQL \d shipments_incomingshipment, вывод подтвердил наличие всех колонок, индексов, внешних ключей.
Административная панель Django настроена для управления данными. Файл core/admin.py:
from django.contrib import admin
from .models import Office, Employee, ShipmentType, CourierService, EventLog

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'address']
    search_fields = ['name', 'code']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['personnel_number', 'full_name', 'position', 'department', 'office', 'is_active']
    list_filter = ['office', 'is_active']
    search_fields = ['personnel_number', 'full_name']

@admin.register(ShipmentType)
class ShipmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(CourierService)
class CourierServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']

@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'event_type', 'ip_address']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['user__username', 'description']
