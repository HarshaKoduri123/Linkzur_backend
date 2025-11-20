from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Unicode font
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))


def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("DejaVu", 18)
    c.drawCentredString(300, 800, "INVOICE")

    c.setFont("DejaVu", 12)
    c.drawString(50, 770, f"Invoice No: {invoice.invoice_number}")
    c.drawString(50, 750, f"Issue Date: {invoice.issue_date}")
    c.drawString(50, 730, f"Buyer: {invoice.buyer.email}")
    c.drawString(50, 710, f"Seller: {invoice.seller.email}")

    # =====================
    # TABLE HEADER
    # =====================
    y = 680
    c.setFont("DejaVu", 12)
    c.drawString(50, y, "Product Details")
    c.drawString(450, y, "Totals")

    # =====================
    # ITEMS LOOP
    # =====================
    for item in invoice.order.items.all():
        y -= 30

        product_name = item.product.name
        variant_label = item.variant.variant_label if item.variant else "Default"

        # Base & discount
        base_price = item.variant.price or item.variant.est_price
        discount = item.product.discount or 0
        discounted_price = item.price  # already discounted in backend
        saved = (base_price - discounted_price) * item.quantity if discount > 0 else 0

        # Product Name
        c.setFont("DejaVu", 12)
        c.drawString(50, y, f"{product_name} ({variant_label})")

        # Original Price (strikethrough)
        if discount > 0:
            y -= 20
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(50, y, f"Original Price: ₹{base_price:.2f}")
            c.line(50, y + 3, 160, y + 3)

            # Discounted price
            c.setFillColorRGB(0, 0, 0)
            c.drawString(200, y, f"Discounted: ₹{discounted_price:.2f}")
            c.drawString(350, y, f"Discount: {discount}% OFF")

        else:
            y -= 20
            c.drawString(50, y, f"Price: ₹{discounted_price:.2f}")

        # Qty and Total
        y -= 20
        c.drawString(50, y, f"Qty: {item.quantity}")
        c.drawString(200, y, f"Line Total: ₹{discounted_price * item.quantity:.2f}")

        # Savings
        if saved > 0:
            y -= 20
            c.setFillColorRGB(0.1, 0.6, 0.1)
            c.drawString(50, y, f"You Saved: ₹{saved:.2f}")
            c.setFillColorRGB(0, 0, 0)

        y -= 10  # spacing

        if y < 120:  # auto new page
            c.showPage()
            c.setFont("DejaVu", 12)
            y = 780

    # =====================
    # TOTALS
    # =====================
    y -= 40
    c.setFont("DejaVu", 12)
    c.drawRightString(550, y, f"Subtotal: ₹{invoice.subtotal}")
    y -= 20
    c.drawRightString(550, y, f"Tax (18%): ₹{invoice.tax_amount}")
    y -= 20
    c.setFont("DejaVu", 13)
    c.drawRightString(550, y, f"TOTAL AMOUNT: ₹{invoice.total_amount}")

    c.showPage()
    c.save()
    buffer.seek(0)

    return ContentFile(buffer.getvalue())
