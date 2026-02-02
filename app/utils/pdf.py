from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime

def generate_receipt(payment_data):
    """
    Generates a PDF receipt for the given payment data.
    payment_data expected keys:
    - transaction_id
    - date (datetime object or string)
    - tenant_name
    - tenant_room
    - amount
    - month
    - payment_mode
    - owner_name (optional)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#1e293b"),
        alignment=1, # Center
        spaceAfter=30
    )
    
    normal_style = styles["Normal"]
    normal_style.fontSize = 12
    normal_style.textColor = colors.HexColor("#334155")
    
    elements = []
    
    # -- Header --
    elements.append(Paragraph("RENT RECEIPT", title_style))
    elements.append(Spacer(1, 12))
    
    # -- Meta Info Grid --
    # Date and Receipt No
    date_str = payment_data.get('date')
    if isinstance(date_str, datetime):
        date_str = date_str.strftime("%d %b, %Y")
        
    meta_data = [
        [f"Receipt No: #{str(payment_data.get('transaction_id'))[:8].upper()}", f"Date: {date_str}"]
    ]
    meta_table = Table(meta_data, colWidths=[230, 230])
    meta_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#64748b")),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))
    
    # -- Main Content --
    elements.append(Paragraph(f"Received with thanks from <b>{payment_data.get('tenant_name')}</b>", normal_style))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph(f"The sum of <b>INR {payment_data.get('amount')}</b>", normal_style))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph(f"Towards Rent for the month of <b>{payment_data.get('month')}</b>", normal_style))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph(f"For Room No: <b>{payment_data.get('tenant_room')}</b>", normal_style))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph(f"Paid via: <b>{payment_data.get('payment_mode')}</b>", normal_style))
    elements.append(Spacer(1, 30))
    
    # -- Amount Box --
    amount_data = [
        ["TOTAL AMOUNT PAID", f"₹ {payment_data.get('amount')}"]
    ]
    amount_table = Table(amount_data, colWidths=[300, 160])
    amount_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0,0), (0,0), colors.HexColor("#64748b")),
        ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#0f172a")),
        ('FONTSIZE', (0,0), (-1,-1), 14),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    elements.append(amount_table)
    elements.append(Spacer(1, 50))
    
    # -- Footer --
    if payment_data.get('owner_name'):
        elements.append(Paragraph(f"Signed by: {payment_data.get('owner_name')}", normal_style))
        elements.append(Spacer(1, 5))
        
    elements.append(Paragraph("Authorized Signatory", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("This is a computer generated receipt.", styles["Italic"]))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
