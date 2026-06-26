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
