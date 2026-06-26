from django.test import TestCase
from shipments.models import IncomingShipment
from core.models import Employee, Office, ShipmentType
from django.contrib.auth.models import User
import datetime

class IncomingShipmentModelTest(TestCase):
    def setUp(self):
        self.office = Office.objects.create(name='Москва', code='MSK', address='ул. Профсоюзная, д. 1')
        self.shipment_type = ShipmentType.objects.create(name='Письмо')
        self.employee = Employee.objects.create(
            personnel_number='001',
            full_name='Иванов Иван Иванович',
            position='Инженер',
            department='Технический отдел',
            office=self.office,
            email='ivanov@norginstroy.ru'
        )
        self.user = User.objects.create_user(username='secretary', password='password123')
    def test_generate_tracking_number(self):
        shipment = IncomingShipment(
            received_date=datetime.date.today(),
            shipment_type=self.shipment_type,
            sender='ООО Контрагент',
            recipient=self.employee,
            office=self.office,
            registered_by=self.user
        )
        shipment.save()
        expected_tracking = datetime.date.today().strftime('%Y%m%d') + '-0001'
        self.assertEqual(shipment.tracking_number, expected_tracking)
    def test_status_default(self):
        shipment = IncomingShipment.objects.create(
            received_date=datetime.date.today(),
            shipment_type=self.shipment_type,
            sender='ООО Контрагент',
            recipient=self.employee,
            office=self.office,
            registered_by=self.user
        )
        self.assertEqual(shipment.status, 'Зарегистрировано')
