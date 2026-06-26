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

    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    p.setFont('DejaVuSans', 12)

    p.drawString(2*cm, height - 2*cm, f'Реестр входящих отправлений за период {date_from} - {date_to}')
    p.setFont('DejaVuSans', 10)

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
