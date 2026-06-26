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
