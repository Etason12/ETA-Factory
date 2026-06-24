import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import qrcode


DARK = HexColor('#1a237e')
ACCENT = HexColor('#3949ab')
GRAY = HexColor('#666666')
LIGHT_GRAY = HexColor('#f5f5f5')
WHITE = HexColor('#ffffff')
BLACK = HexColor('#000000')


def _init_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('CompanyName', parent=styles['Heading1'], fontSize=18, textColor=BLACK, spaceAfter=2, alignment=TA_CENTER))
    styles.add(ParagraphStyle('CompanyInfo', parent=styles['Normal'], fontSize=8, textColor=BLACK, alignment=TA_CENTER, spaceAfter=1))
    styles.add(ParagraphStyle('ReceiptTitle', parent=styles['Heading2'], fontSize=16, textColor=BLACK, alignment=TA_CENTER, spaceBefore=8, spaceAfter=12))
    styles.add(ParagraphStyle('SectionLabel', parent=styles['Normal'], fontSize=8, textColor=BLACK, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle('SectionValue', parent=styles['Normal'], fontSize=9, textColor=BLACK))
    styles.add(ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=8, textColor=BLACK, fontName='Helvetica-Bold', alignment=TA_CENTER))
    styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=8, textColor=BLACK, alignment=TA_CENTER))
    styles.add(ParagraphStyle('TableCellLeft', parent=styles['Normal'], fontSize=8, textColor=BLACK, alignment=TA_LEFT))
    styles.add(ParagraphStyle('TableCellRight', parent=styles['Normal'], fontSize=8, textColor=BLACK, alignment=TA_RIGHT))
    styles.add(ParagraphStyle('FooterText', parent=styles['Normal'], fontSize=7, textColor=GRAY, alignment=TA_CENTER))
    return styles


def generate_receipt(payment, invoice, sales_order, customer, items, company=None):
    s = _init_styles()
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=15*mm, rightMargin=15*mm
    )

    elements = []

    company_name = company.name if company else 'Company Name'
    company_info = []
    if company:
        if company.address:
            company_info.append(company.address)
        parts = []
        if company.phone:
            parts.append(f'Tel: {company.phone}')
        if company.email:
            parts.append(f'Email: {company.email}')
        if parts:
            company_info.append(' | '.join(parts))
        if company.tax_id:
            company_info.append(f'TIN: {company.tax_id}')

    elements.append(Paragraph(company_name, s['CompanyName']))
    for line in company_info:
        elements.append(Paragraph(line, s['CompanyInfo']))

    elements.append(Spacer(1, 2*mm))

    line_style = TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, DARK),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, ACCENT),
    ])
    elements.append(Table([['']], colWidths=[170*mm], style=line_style))

    elements.append(Paragraph('PAYMENT RECEIPT', s['ReceiptTitle']))

    group_data = [
        [Paragraph('Receipt #', s['SectionLabel']), Paragraph(payment.payment_number, s['SectionValue']),
         Paragraph('Date', s['SectionLabel']), Paragraph(payment.payment_date.isoformat() if payment.payment_date else date.today().isoformat(), s['SectionValue'])],
        [Paragraph('Payment Method', s['SectionLabel']), Paragraph(payment.payment_method, s['SectionValue']),
         Paragraph('Invoice #', s['SectionLabel']), Paragraph(invoice.invoice_number, s['SectionValue'])],
    ]
    if payment.reference_number:
        group_data.append([
            Paragraph('Reference #', s['SectionLabel']), Paragraph(payment.reference_number, s['SectionValue']), '', ''
        ])
    group_data.append([
        Paragraph('Customer', s['SectionLabel']), Paragraph(customer.name, s['SectionValue']),
        Paragraph('Code', s['SectionLabel']), Paragraph(customer.customer_code, s['SectionValue']),
    ])
    if customer.phone:
        group_data.append([Paragraph('Phone', s['SectionLabel']), Paragraph(customer.phone, s['SectionValue']), '', ''])
    if customer.tin_number:
        group_data.append([Paragraph('TIN', s['SectionLabel']), Paragraph(customer.tin_number, s['SectionValue']), '', ''])
    if customer.address:
        group_data.append([Paragraph('Address', s['SectionLabel']), Paragraph(customer.address, s['SectionValue']), '', ''])
    group_data.append([
        Paragraph('Sales Order', s['SectionLabel']), Paragraph(sales_order.order_number, s['SectionValue']),
        Paragraph('Order Date', s['SectionLabel']), Paragraph(sales_order.order_date.isoformat() if sales_order.order_date else '', s['SectionValue']),
    ])

    elements.append(Table(group_data, colWidths=[28*mm, 52*mm, 25*mm, 65*mm],
                          style=TableStyle([
                              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('TOPPADDING', (0, 0), (-1, -1), 2),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                              ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#dddddd')),
                          ])))
    elements.append(Spacer(1, 4*mm))

    header = [Paragraph('SN', s['TableHeader']), Paragraph('Item', s['TableHeader']),
              Paragraph('Qty', s['TableHeader']), Paragraph('Unit Price', s['TableHeader']),
              Paragraph('Total', s['TableHeader'])]
    body = [header]
    for idx, item in enumerate(items, 1):
        qty = float(item.quantity)
        unit_price = float(item.unit_price)
        total = float(item.total_price)
        product_name = item.product.name if item.product else f'Product #{item.product_id}'
        body.append([
            Paragraph(str(idx), s['TableCell']),
            Paragraph(product_name, s['TableCellLeft']),
            Paragraph(f'{qty:,.2f}', s['TableCell']),
            Paragraph(f'{unit_price:,.2f}', s['TableCellRight']),
            Paragraph(f'{total:,.2f}', s['TableCellRight']),
        ])

    currency = company.currency if company and company.currency else 'ETB'

    body.append(['', '', '', Paragraph('Subtotal', s['TableCellRight']),
                 Paragraph(f'{currency} {float(invoice.subtotal or 0):,.2f}', s['TableCellRight'])])
    body.append(['', '', '', Paragraph('Total', s['TableHeader']),
                 Paragraph(f'{currency} {float(invoice.total_amount or 0):,.2f}', s['TableCellRight'])])
    body.append(['', '', '', Paragraph('Paid', s['TableCellRight']),
                 Paragraph(f'{currency} {float(payment.amount or 0):,.2f}', s['TableCellRight'])])
    body.append(['', '', '', Paragraph('Balance Due', s['TableCellRight']),
                 Paragraph(f'{currency} {float(invoice.balance_due or 0):,.2f}', s['TableCellRight'])])

    col_w = [12*mm, 62*mm, 28*mm, 34*mm, 34*mm]
    tbl = Table(body, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), BLACK),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -4), 0.3, HexColor('#cccccc')),
        ('LINEABOVE', (0, -4), (-1, -4), 0.5, ACCENT),
        ('LINEABOVE', (0, -3), (-1, -3), 0.5, ACCENT),
        ('LINEABOVE', (0, -2), (-1, -2), 0.5, DARK),
        ('LINEBELOW', (0, -2), (-1, -2), 1, DARK),
        ('LINEABOVE', (0, -1), (-1, -1), 0.3, HexColor('#cccccc')),
        ('LINEBELOW', (0, -1), (-1, -1), 0.3, HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -4), LIGHT_GRAY),
        ('BACKGROUND', (0, -3), (-1, -3), HexColor('#e8eaf6')),
        ('BACKGROUND', (0, -2), (-1, -2), HexColor('#c5cae9')),
    ]))
    elements.append(tbl)

    qr = qrcode.QRCode(box_size=3, border=1)
    qr_data = (
        f'Payment: {payment.payment_number}\n'
        f'Date: {payment.payment_date.isoformat() if payment.payment_date else ""}\n'
        f'Invoice: {invoice.invoice_number}\n'
        f'Customer: {customer.name}\n'
        f'Amount: {currency} {float(payment.amount):,.2f}'
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white')

    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    elements.append(Spacer(1, 6*mm))

    qr_table = Table([
        [Image(qr_buf, width=30*mm, height=30*mm),
         Paragraph('Thank you for your business!<br/>This is a computer-generated receipt.', s['FooterText'])]
    ], colWidths=[40*mm, 130*mm])
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
    ]))
    elements.append(qr_table)

    doc.build(elements)
    buf.seek(0)
    return buf
