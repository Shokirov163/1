from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import IncomingShipment
from .forms import IncomingShipmentForm

class ShipmentRegisterView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = IncomingShipment
    form_class = IncomingShipmentForm
    template_name = 'shipments/shipment_register.html'
    success_url = reverse_lazy('shipments:list')
    permission_required = 'shipments.add_incomingshipment'

    def form_valid(self, form):
        form.instance.registered_by = self.request.user
        return super().form_valid(form)
Форма (shipments/forms.py):
from django import forms
from .models import IncomingShipment
from core.models import Employee
import datetime

class IncomingShipmentForm(forms.ModelForm):
    class Meta:
        model = IncomingShipment
        fields = ['received_date', 'shipment_type', 'sender', 'recipient', 'office', 'notes']
        widgets = {
            'received_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'shipment_type': forms.Select(attrs={'class': 'form-select'}),
            'sender': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название организации или ФИО'}),
            'recipient': forms.Select(attrs={'class': 'form-select'}),
            'office': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipient'].queryset = Employee.objects.filter(is_active=True)

    def clean_received_date(self):
        received_date = self.cleaned_data['received_date']
        if received_date > datetime.date.today():
            raise forms.ValidationError('Дата поступления не может быть в будущем')
        return received_date

    def clean(self):
        cleaned_data = super().clean()
        recipient = cleaned_data.get('recipient')
        if recipient and not recipient.is_active:
            raise forms.ValidationError('Выбранный получатель не является активным сотрудником')
        return cleaned_data
Шаблон (shipments/templates/shipments/shipment_register.html):
{% extends 'base.html' %}
{% load static %}

{% block title %}Регистрация входящего отправления{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>Регистрация входящего отправления</h2>
    <form method="post" class="mt-3">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-primary">Сохранить</button>
        <a href="{% url 'shipments:list' %}" class="btn btn-secondary">Отмена</a>
    </form>
</div>
{% endblock %}
Базовый шаблон (templates/base.html) содержит структуру HTML-страницы, навигационное меню, подключение Bootstrap CSS и JavaScript:
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Система учета почты{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'home' %}">Учет почты НорГринСтрой</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item"><a class="nav-link" href="{% url 'shipments:register' %}">Регистрация</a></li>
                    <li class="nav-item"><a class="nav-link" href="{% url 'shipments:list' %}">Поиск</a></li>
                    <li class="nav-item"><a class="nav-link" href="{% url 'reports:incoming' %}">Отчеты</a></li>
                    <li class="nav-item"><a class="nav-link" href="{% url 'reports:statistics' %}">Статистика</a></li>
                </ul>
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><span class="navbar-text">{{ request.user.username }}</span></li>
                    <li class="nav-item"><a class="nav-link" href="{% url 'logout' %}">Выход</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <main>
        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
Представление списка отправлений с поиском (shipments/views.py):
from django.views.generic import ListView
from .models import IncomingShipment

class ShipmentListView(LoginRequiredMixin, ListView):
    model = IncomingShipment
    template_name = 'shipments/shipment_list.html'
    context_object_name = 'shipments'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        tracking_number = self.request.GET.get('tracking_number', '')
        sender = self.request.GET.get('sender', '')
        recipient_id = self.request.GET.get('recipient', '')
        office_id = self.request.GET.get('office', '')
        status = self.request.GET.get('status', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')

        if tracking_number:
            queryset = queryset.filter(tracking_number__icontains=tracking_number)
        if sender:
            queryset = queryset.filter(sender__icontains=sender)
        if recipient_id:
            queryset = queryset.filter(recipient_id=recipient_id)
        if office_id:
            queryset = queryset.filter(office_id=office_id)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(received_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(received_date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = Employee.objects.filter(is_active=True)
        context['offices'] = Office.objects.all()
        context['statuses'] = IncomingShipment.STATUS_CHOICES
        return context
Шаблон списка (shipments/templates/shipments/shipment_list.html) содержит форму поиска с полями для каждого фильтра и таблицу результатов с пагинацией:
{% extends 'base.html' %}

{% block title %}Поиск отправлений{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>Поиск отправлений</h2>
    <form method="get" class="row g-3 mt-2">
        <div class="col-md-3">
            <label for="tracking_number" class="form-label">Идентификатор</label>
            <input type="text" class="form-control" id="tracking_number" name="tracking_number" value="{{ request.GET.tracking_number }}">
        </div>
        <div class="col-md-3">
            <label for="sender" class="form-label">Отправитель</label>
            <input type="text" class="form-control" id="sender" name="sender" value="{{ request.GET.sender }}">
        </div>
        <div class="col-md-3">
            <label for="recipient" class="form-label">Получатель</label>
            <select class="form-select" id="recipient" name="recipient">
                <option value="">Все</option>
                {% for employee in employees %}
                <option value="{{ employee.id }}" {% if request.GET.recipient == employee.id|stringformat:"s" %}selected{% endif %}>{{ employee.full_name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="col-md-3">
            <label for="office" class="form-label">Офис</label>
            <select class="form-select" id="office" name="office">
                <option value="">Все</option>
                {% for office in offices %}
                <option value="{{ office.id }}" {% if request.GET.office == office.id|stringformat:"s" %}selected{% endif %}>{{ office.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="col-md-3">
            <label for="status" class="form-label">Статус</label>
            <select class="form-select" id="status" name="status">
                <option value="">Все</option>
                {% for value, label in statuses %}
                <option value="{{ value }}" {% if request.GET.status == value %}selected{% endif %}>{{ label }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="col-md-3">
            <label for="date_from" class="form-label">Дата с</label>
            <input type="date" class="form-control" id="date_from" name="date_from" value="{{ request.GET.date_from }}">
        </div>
        <div class="col-md-3">
            <label for="date_to" class="form-label">Дата по</label>
            <input type="date" class="form-control" id="date_to" name="date_to" value="{{ request.GET.date_to }}">
        </div>
        <div class="col-md-3 d-flex align-items-end">
            <button type="submit" class="btn btn-primary me-2">Найти</button>
            <a href="{% url 'shipments:list' %}" class="btn btn-secondary">Сбросить</a>
        </div>
    </form>

    <table class="table table-striped mt-4">
        <thead>
            <tr>
                <th>Идентификатор</th>
                <th>Дата</th>
                <th>Отправитель</th>
                <th>Получатель</th>
                <th>Офис</th>
                <th>Тип</th>
                <th>Статус</th>
                <th>Действия</th>
            </tr>
        </thead>
        <tbody>
            {% for shipment in shipments %}
            <tr>
                <td>{{ shipment.tracking_number }}</td>
                <td>{{ shipment.received_date }}</td>
                <td>{{ shipment.sender }}</td>
                <td>{{ shipment.recipient.full_name }}</td>
                <td>{{ shipment.office.name }}</td>
                <td>{{ shipment.shipment_type.name }}</td>
                <td>{{ shipment.get_status_display }}</td>
                <td>
                    <a href="{% url 'shipments:detail' shipment.pk %}" class="btn btn-sm btn-info">Подробнее</a>
                    {% if shipment.status != 'Получено' %}
                    <a href="{% url 'shipments:mark_received' shipment.pk %}" class="btn btn-sm btn-success">Получено</a>
                    {% endif %}
                </td>
            </tr>
            {% empty %}
            <tr><td colspan="8" class="text-center">Отправления не найдены</td></tr>
            {% endfor %}
        </tbody>
    </table>

    {% if is_paginated %}
    <nav>
        <ul class="pagination">
            {% if page_obj.has_previous %}
            <li class="page-item"><a class="page-link" href="?page=1">Первая</a></li>
            <li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">Предыдущая</a></li>
            {% endif %}
            <li class="page-item disabled"><span class="page-link">Страница {{ page_obj.number }} из {{ page_obj.paginator.num_pages }}</span></li>
            {% if page_obj.has_next %}
            <li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">Следующая</a></li>
            <li class="page-item"><a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">Последняя</a></li>
            {% endif %}
        </ul>
    </nav>
    {% endif %}
</div>
{% endblock %}
Представление отметки о получении реализовано как функциональное представление:
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from .models import IncomingShipment

@login_required
@permission_required('shipments.change_incomingshipment', raise_exception=True)
def shipment_mark_received(request, pk):
    shipment = get_object_or_404(IncomingShipment, pk=pk)
    shipment.status = 'Получено'
    shipment.received_by = request.user
    shipment.received_at = timezone.now()
    shipment.save()
    return redirect('shipments:detail', pk=pk)
Представление детальной информации об отправлении:
from django.views.generic import DetailView

class ShipmentDetailView(LoginRequiredMixin, DetailView):
    model = IncomingShipment
    template_name = 'shipments/shipment_detail.html'
    context_object_name = 'shipment'
Сервис отправки уведомлений (shipments/services.py):
from django.core.mail import send_mail
from django.conf import settings
from .models import IncomingShipment

class NotificationService:
    @staticmethod
    def send_shipment_notification(shipment_id):
        try:
            shipment = IncomingShipment.objects.get(id=shipment_id)
            if not shipment.recipient.email:
                return False

            subject = f'Для Вас поступило отправление {shipment.tracking_number}'
            message = f"""
Здравствуйте, {shipment.recipient.full_name}!

Для Вас поступило отправление:
Идентификатор: {shipment.tracking_number}
Дата поступления: {shipment.received_date}
Тип: {shipment.shipment_type.name}
Отправитель: {shipment.sender}

Вы можете забрать отправление в приемной офиса {shipment.office.name}.

С уважением,
Система учета почты НорГринСтрой
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [shipment.recipient.email],
                fail_silently=False,
            )
            shipment.notification_sent = True
            shipment.save(update_fields=['notification_sent'])
            return True
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
            return False
Обработчик сигнала для автоматической отправки уведомлений (shipments/signals.py):
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IncomingShipment
from .services import NotificationService

@receiver(post_save, sender=IncomingShipment)
def send_notification_on_create(sender, instance, created, **kwargs):
    if created and instance.recipient.email:
        NotificationService.send_shipment_notification(instance.id)
Регистрация обработчика в shipments/apps.py:
from django.apps import AppConfig

class ShipmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shipments'

    def ready(self):
        import shipments.signals
Конфигурация email в settings.py:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.norginstroy.local'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'mailsystem@norginstroy.ru'
Внутренний SMTP-сервер НорГринСтрой настроен на прием писем от системы учета почты без аутентификации (доверенный хост 127.0.0.1).
Сервис синхронизации сотрудников с «1С» (core/services.py):
import requests
from django.conf import settings
from .models import Employee, Office

class EmployeeSyncService:
    @staticmethod
    def sync_from_1c():
        try:
            response = requests.get(f"{settings.ONE_C_API_URL}/employees/", timeout=30)
            response.raise_for_status()
            employees_data = response.json()

            for emp_data in employees_data:
                office = Office.objects.get(code=emp_data['office_code'])
                Employee.objects.update_or_create(
                    personnel_number=emp_data['personnel_number'],
                    defaults={
                        'full_name': emp_data['full_name'],
                        'position': emp_data['position'],
                        'department': emp_data['department'],
                        'office': office,
                        'phone': emp_data.get('phone', ''),
                        'email': emp_data.get('email', ''),
                        'is_active': emp_data.get('is_active', True),
                    }
                )
            return True
        except Exception as e:
            print(f"Ошибка синхронизации с 1С: {e}")
            return False
Конфигурация URL API «1С» в settings.py:
ONE_C_API_URL = 'http://1c-server.norginstroy.local/api'
Планировщик задач Celery настроен для ежедневной синхронизации (mailsystem/celery.py):
from celery import Celery
from celery.schedules import crontab

app = Celery('mailsystem')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'sync-employees-daily': {
        'task': 'core.tasks.sync_employees',
        'schedule': crontab(hour=8, minute=0),
    },
}
Задача Celery (core/tasks.py):
from celery import shared_task
from .services import EmployeeSyncService

@shared_task
def sync_employees():
    return EmployeeSyncService.sync_from_1c()
Celery использует Redis в качестве брокера сообщений. Конфигурация в settings.py:
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
Redis установлен и запущен на сервере командой sudo apt install redis-server && sudo systemctl enable redis-server.
Формирование отчетов реализовано в приложении reports. Представление отчета входящих отправлений (reports/views.py):
from django.views.generic import FormView
from django.http import HttpResponse
from .forms import IncomingShipmentReportForm
from .generators import generate_pdf_report, generate_excel_report
from shipments.models import IncomingShipment

class IncomingShipmentReportView(LoginRequiredMixin, FormView):
    form_class = IncomingShipmentReportForm
    template_name = 'reports/incoming_shipment_report.html'

    def form_valid(self, form):
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
        office = form.cleaned_data.get('office')
        shipment_type = form.cleaned_data.get('shipment_type')
        status = form.cleaned_data.get('status')
        export_format = form.cleaned_data['export_format']

        queryset = IncomingShipment.objects.filter(received_date__gte=date_from, received_date__lte=date_to)
        if office:
            queryset = queryset.filter(office=office)
        if shipment_type:
            queryset = queryset.filter(shipment_type=shipment_type)
        if status:
            queryset = queryset.filter(status=status)

        if export_format == 'pdf':
            return generate_pdf_report(queryset, date_from, date_to)
        elif export_format == 'excel':
            return generate_excel_report(queryset, date_from, date_to)
Форма отчета (reports/forms.py):
from django import forms
from core.models import Office, ShipmentType
from shipments.models import IncomingShipment

class IncomingShipmentReportForm(forms.Form):
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]

    date_from = forms.DateField(label='Дата с', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_to = forms.DateField(label='Дата по', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    office = forms.ModelChoiceField(queryset=Office.objects.all(), required=False, label='Офис',
                                    widget=forms.Select(attrs={'class': 'form-select'}))
    shipment_type = forms.ModelChoiceField(queryset=ShipmentType.objects.all(), required=False, label='Тип отправления',
                                           widget=forms.Select(attrs={'class': 'form-select'}))
    status = forms.ChoiceField(choices=[('', 'Все')] + IncomingShipment.STATUS_CHOICES, required=False, label='Статус',
                               widget=forms.Select(attrs={'class': 'form-select'}))
    export_format = forms.ChoiceField(choices=EXPORT_FORMATS, label='Формат экспорта',
                                      widget=forms.Select(attrs={'class': 'form-select'}))

Генератор PDF-отчета (reports/generators.py):
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import HttpResponse
from io import BytesIO
import datetime

def generate_pdf_report(queryset, date_from, date_to):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Регистрация шрифта с поддержкой кириллицы
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    p.setFont('DejaVuSans', 12)

    # Заголовок
    p.drawString(2*cm, height - 2*cm, f'Реестр входящих отправлений за период {date_from} - {date_to}')
    p.setFont('DejaVuSans', 10)

    # Таблица
    y = height - 3*cm
    headers = ['№', 'Идентификатор', 'Дата', 'Отправитель', 'Получатель', 'Офис', 'Тип', 'Статус']
    x_positions = [1*cm, 2*cm, 6*cm, 9*cm, 13*cm, 18*cm, 21*cm, 24*cm]

    for i, header in enumerate(headers):
        p.drawString(x_positions[i], y, header)

    y -= 0.5*cm
    for idx, shipment in enumerate(queryset, start=1):
        if y < 2*cm:
            p.showPage()
            p.setFont('DejaVuSans', 10)
            y = height - 2*cm

        p.drawString(x_positions[0], y, str(idx))
        p.drawString(x_positions[1], y, shipment.tracking_number)
        p.drawString(x_positions[2], y, str(shipment.received_date))
        p.drawString(x_positions[3], y, shipment.sender[:20])
        p.drawString(x_positions[4], y, shipment.recipient.full_name[:25])
        p.drawString(x_positions[5], y, shipment.office.code)
        p.drawString(x_positions[6], y, shipment.shipment_type.name[:15])
        p.drawString(x_positions[7], y, shipment.get_status_display()[:15])
        y -= 0.5*cm

    # Итоги
    y -= 0.5*cm
    p.drawString(2*cm, y, f'Всего записей: {queryset.count()}')
    y -= 0.5*cm
    p.drawString(2*cm, y, f'Дата формирования: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}')

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="incoming_shipments_{date_from}_{date_to}.pdf"'
    return response


Генератор Excel-отчета:
from openpyxl import Workbook
from django.http import HttpResponse
from io import BytesIO

def generate_excel_report(queryset, date_from, date_to):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Входящие отправления'

    # Заголовок
    ws.append([f'Реестр входящих отправлений за период {date_from} - {date_to}'])
    ws.append([])

    # Заголовки таблицы
    headers = ['№', 'Идентификатор', 'Дата поступления', 'Отправитель', 'Получатель', 'Офис', 'Тип', 'Статус']
    ws.append(headers)

    # Данные
    for idx, shipment in enumerate(queryset, start=1):
        ws.append([
            idx,
            shipment.tracking_number,
            shipment.received_date.strftime('%d.%m.%Y'),
            shipment.sender,
            shipment.recipient.full_name,
            shipment.office.name,
            shipment.shipment_type.name,
            shipment.get_status_display(),
        ])

    # Итоги
    ws.append([])
    ws.append([f'Всего записей: {queryset.count()}'])
    ws.append([f'Дата формирования: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}'])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="incoming_shipments_{date_from}_{date_to}.xlsx"'
    return response
Журналирование действий пользователей реализовано middleware (core/middleware.py):
from .models import EventLog

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.method == 'POST':
            event_type = self._get_event_type(request.path)
            if event_type:
                EventLog.objects.create(
                    user=request.user,
                    event_type=event_type,
                    description=f"{request.method} {request.path}",
                    ip_address=self._get_client_ip(request),
                )

        return response

    def _get_event_type(self, path):
        if '/register/' in path:
            return 'Регистрация отправления'
        elif '/mark_received/' in path:
            return 'Изменение статуса'
        elif '/reports/' in path:
            return 'Формирование отчета'
        return None

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
Middleware добавлен в MIDDLEWARE в settings.py:
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.LoggingMiddleware',
]


Маршрутизация URL (mailsystem/urls.py):
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shipments.urls')),
    path('reports/', include('reports.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]
Маршруты приложения shipments (shipments/urls.py):
from django.urls import path
from . import views

app_name = 'shipments'

urlpatterns = [
    path('', views.ShipmentListView.as_view(), name='list'),
    path('register/', views.ShipmentRegisterView.as_view(), name='register'),
    path('<int:pk>/', views.ShipmentDetailView.as_view(), name='detail'),
    path('<int:pk>/mark_received/', views.shipment_mark_received, name='mark_received'),
]
Развертывание системы на сервере выполнено следующим образом. Установка зависимостей через pip:
pip install django==4.2 psycopg2-binary gunicorn celery redis reportlab openpyxl requests
Конфигурация Gunicorn (/etc/systemd/system/mailsystem.service):
[Unit]
Description=Gunicorn daemon for mailsystem
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mailsystem
ExecStart=/usr/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 mailsystem.wsgi:application

[Install]
WantedBy=multi-user.target
Конфигурация Nginx (/etc/nginx/sites-available/mailsystem):
server {
    listen 443 ssl;
    server_name mailsystem.norginstroy.local;

    ssl_certificate /etc/nginx/ssl/mailsystem.crt;
    ssl_certificate_key /etc/nginx/ssl/mailsystem.key;

    location /static/ {
        alias /var/www/mailsystem/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
Сборка статических файлов:
python manage.py collectstatic --noinput

Запуск служб:
sudo systemctl start mailsystem
sudo systemctl enable mailsystem
sudo systemctl restart nginx
celery -A mailsystem worker --loglevel=info &
celery -A mailsystem beat --loglevel=info &


Создание суперпользователя и групп:
python manage.py createsuperuser
python manage.py shell
>>> from django.contrib.auth.models import Group, Permission
>>> admin_group = Group.objects.create(name='Администратор')
>>> secretary_group = Group.objects.create(name='Секретарь')
>>> employee_group = Group.objects.create(name='Сотрудник')
>>> manager_group = Group.objects.create(name='Руководитель')
>>> # Назначение разрешений группам (add, change, view для соответствующих моделей)
