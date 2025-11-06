from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 800, "INVOICE")

    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Invoice No: {invoice.invoice_number}")
    c.drawString(50, 750, f"Issue Date: {invoice.issue_date}")
    c.drawString(50, 730, f"Buyer: {invoice.buyer.email}")
    c.drawString(50, 710, f"Seller: {invoice.seller.email}")

    y = 670
    c.drawString(50, y, "Product")
    c.drawString(250, y, "Qty")
    c.drawString(350, y, "Price")
    c.drawString(450, y, "Total")

    for item in invoice.order.items.all():
        y -= 20
        c.drawString(50, y, item.product.name)
        c.drawString(250, y, str(item.quantity))
        c.drawString(350, y, f"₹{item.price}")
        c.drawString(450, y, f"₹{item.price * item.quantity}")

    y -= 40
    c.drawRightString(550, y, f"Subtotal: ₹{invoice.subtotal}")
    y -= 20
    c.drawRightString(550, y, f"Tax (18%): ₹{invoice.tax_amount}")
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(550, y, f"Total: ₹{invoice.total_amount}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return ContentFile(buffer.getvalue())
