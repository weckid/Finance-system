"""
Генерация отчетов в форматах Excel и PDF.
"""

import pandas as pd
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime


def generate_excel_report(user, start_date, end_date):
    """Генерация Excel отчета"""
    from .models import Transaction

    transactions = Transaction.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).values('date', 'type', 'category__name', 'amount', 'description')

    df = pd.DataFrame(list(transactions))

    # Создание Excel файла
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Транзакции', index=False)

        # Сводная таблица
        pivot = pd.pivot_table(df, values='amount',
                               index='category__name',
                               columns='type',
                               aggfunc='sum',
                               fill_value=0)
        pivot.to_excel(writer, sheet_name='Сводка')

    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    return response


def generate_pdf_report(user, start_date, end_date):
    """Генерация PDF отчета"""
    from .models import Transaction

    transactions = Transaction.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Отчет по транзакциям", styles['Title']))
    elements.append(Paragraph(f"Период: {start_date} - {end_date}", styles['Normal']))
    elements.append(Paragraph(f"Пользователь: {user.username}", styles['Normal']))

    # Таблица транзакций
    data = [['Дата', 'Тип', 'Категория', 'Сумма', 'Описание']]

    for t in transactions:
        data.append([
            t.date.strftime('%d.%m.%Y'),
            t.get_type_display(),
            t.category.name if t.category else '-',
            f"{t.amount} ₽",
            t.description[:50]
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='application/pdf')