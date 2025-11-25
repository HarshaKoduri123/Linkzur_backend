from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.units import mm

# Register Unicode Font
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    margin = 40

    # ============================
    # HEADER (INVOICE TITLE)
    # ============================
    c.setFont("DejaVu", 22)
    c.drawString(margin, height - 50, "INVOICE")

    # Divider
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(margin, height - 60, width - margin, height - 60)

    # ============================
    # INVOICE INFO
    # ============================
    c.setFont("DejaVu", 11)
    y = height - 90

    c.drawString(margin, y, f"Invoice Number: {invoice.invoice_number}")
    y -= 16
    c.drawString(margin, y, f"Issue Date: {invoice.issue_date}")

    # ============================
    # BUYER + SELLER + ADDRESS SECTION
    # ============================
    y -= 40
    
    # Seller Block
    c.setFont("DejaVu", 12)
    c.drawString(margin, y, "Seller:")
    c.setFont("DejaVu", 11)
    y -= 16
    c.drawString(margin, y, f"{invoice.seller.email}")

    # Buyer Block
    y -= 30
    c.setFont("DejaVu", 12)
    c.drawString(margin, y, "Buyer:")
    c.setFont("DejaVu", 11)
    y -= 16
    c.drawString(margin, y, f"{invoice.buyer.email}")

    # Shipping Address
    y -= 30
    c.setFont("DejaVu", 12)
    c.drawString(margin, y, "Shipping Address:")
    c.setFont("DejaVu", 11)
    y -= 16

    wrapped_address = invoice.order.address.split("\n") if invoice.order.address else ["N/A"]

    for line in wrapped_address:
        c.drawString(margin, y, line)
        y -= 16

    # Divider
    y -= 10
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.grey)
    c.line(margin, y, width - margin, y)
    y -= 20

    # ============================
    # TABLE HEADER
    # ============================
    c.setFont("DejaVu", 12)
    c.setFillColor(colors.black)

    c.drawString(margin, y, "Product")
    c.drawString(260, y, "Qty")
    c.drawString(330, y, "Price")
    c.drawString(420, y, "Discount")
    c.drawString(500, y, "Total")

    y -= 12
    c.line(margin, y, width - margin, y)
    y -= 20

    # ============================
    # PRODUCT LIST LOOP
    # ============================
    c.setFont("DejaVu", 11)

    for item in invoice.order.items.all():

        product = item.product.name
        variant = item.variant.variant_label if item.variant else "Default"
        qty = item.quantity
        price = item.variant.price or item.variant.est_price or 0
        discount = item.product.discount or 0
        discounted_price = item.price

        total_line = discounted_price * qty

        # Product Name
        c.drawString(margin, y, f"{product} ({variant})")

        # Qty
        c.drawString(265, y, str(qty))

        # Original price
        c.drawString(330, y, f"₹{price:.2f}")

        # Discount
        c.drawString(430, y, f"{discount}%")

        # Line total
        c.drawString(500, y, f"₹{total_line:.2f}")

        y -= 18

        # Auto new page
        if y < 120:
            c.showPage()
            c.setFont("DejaVu", 11)
            y = height - 120

    # ============================
    # TOTALS SUMMARY
    # ============================
    y -= 30
    c.setFont("DejaVu", 12)

    c.drawRightString(width - margin, y, f"Subtotal: ₹{invoice.subtotal:.2f}")
    y -= 20
    c.drawRightString(width - margin, y, f"Tax (18% GST): ₹{invoice.tax_amount:.2f}")
    y -= 20

    c.setFont("DejaVu", 14)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawRightString(width - margin, y, f"TOTAL: ₹{invoice.total_amount:.2f}")

    # Footer Line
    y -= 40
    c.setStrokeColor(colors.black)
    c.line(margin, y, width - margin, y)

    y -= 20
    c.setFont("DejaVu", 10)
    c.drawString(margin, y, "Thank you for your purchase!")

    c.save()
    buffer.seek(0)
    return ContentFile(buffer.getvalue())
