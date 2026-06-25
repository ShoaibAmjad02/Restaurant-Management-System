import json
import qrcode
import qrcode.constants
from io import BytesIO
from django.urls import reverse
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont


CARD_WIDTH = 86 * mm
CARD_HEIGHT = 54 * mm

BLACK_TOP = "#1a1a1a"
BLACK_BOT = "#000000"
ORANGE = "#ff6600"
YELLOW = "#ffd700"
WHITE = "#ffffff"
GRAY = "#aaaaaa"
DIM = "#666666"

QR_BOX_SIZE = 10
QR_BORDER = 4
PNG_QR_SIZE = 250
PDF_QR_SIZE_MM = 25
PNG_CARD_WIDTH = 600
PNG_CARD_HEIGHT = 376


def _build_qr_url(card, request=None):
    path = reverse("users:verify_loyalty_qr", args=[card.qr_token])
    if request:
        return request.build_absolute_uri(path)
    try:
        from django.conf import settings as django_settings
        site_url = getattr(django_settings, "SITE_URL", None)
        if site_url:
            return site_url.rstrip("/") + path
    except Exception:
        pass
    return f"https://loyalty/verify/{card.qr_token}"


def _make_qr_image(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=QR_BOX_SIZE,
        border=QR_BORDER,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img


def generate_qr_code_image(card, request=None):
    url = _build_qr_url(card, request)
    img = _make_qr_image(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    filename = f"qr_{card.card_number}.png"
    card.qr_code_image.save(filename, ContentFile(buf.getvalue()), save=False)
    card.save(update_fields=['qr_code_image'])
    return card


def _get_qr_pil_image(card, request=None, target_size=PNG_QR_SIZE):
    if card.qr_code_image and card.qr_code_image.storage.exists(card.qr_code_image.name):
        try:
            card.qr_code_image.open('rb')
            pil = Image.open(card.qr_code_image)
            if pil.width >= target_size:
                return pil
        except Exception:
            pass
    generate_qr_code_image(card, request)
    if card.qr_code_image and card.qr_code_image.storage.exists(card.qr_code_image.name):
        try:
            card.qr_code_image.open('rb')
            pil = Image.open(card.qr_code_image)
            if pil.width >= target_size:
                return pil
        except Exception:
            pass
    url = _build_qr_url(card, request)
    return _make_qr_image(url)


def _lerp_color(c1, c2, t):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _draw_gradient_background_pdf(c, w, h, color1, color2):
    steps = 60
    for i in range(steps):
        t = i / steps
        color_hex = _lerp_color(color1, color2, t)
        c.setFillColor(HexColor(color_hex))
        strip_h = h / steps
        c.rect(0, i * strip_h, w, strip_h + 0.5, fill=1, stroke=0)


def _draw_gradient_background_pil(draw, w, h, color1, color2):
    steps = 60
    for i in range(steps):
        t = i / steps
        color_hex = _lerp_color(color1, color2, t)
        strip_h = h / steps
        draw.rectangle([0, i * strip_h, w, (i + 1) * strip_h], fill=color_hex)


def _draw_card_border(c, w, h):
    c.setStrokeColor(HexColor(ORANGE))
    c.setLineWidth(0.5)
    c.roundRect(3*mm, 3*mm, w - 6*mm, h - 6*mm, 4*mm, fill=0, stroke=1)
    c.setStrokeColor(HexColor(YELLOW))
    c.setLineWidth(0.2)
    c.roundRect(3.5*mm, 3.5*mm, w - 7*mm, h - 7*mm, 3.5*mm, fill=0, stroke=1)


def generate_loyalty_card_pdf(card, request=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(CARD_WIDTH, CARD_HEIGHT))

    _draw_gradient_background_pdf(c, CARD_WIDTH, CARD_HEIGHT, BLACK_TOP, BLACK_BOT)
    _draw_card_border(c, CARD_WIDTH, CARD_HEIGHT)

    _draw_pdf_logo_section(c)
    _draw_pdf_customer_info(c, card)
    _draw_pdf_points_section(c, card)
    _draw_pdf_qr_section(c, card, request)

    c.save()
    buffer.seek(0)

    filename = f"loyalty_card_{card.card_number}.pdf"
    card.card_pdf.save(filename, ContentFile(buffer.getvalue()), save=False)
    card.save(update_fields=['card_pdf'])
    return card


def _draw_pdf_logo_section(c):
    c.setFillColor(HexColor(ORANGE))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(6*mm, CARD_HEIGHT - 9*mm, "LOGO")

    c.setFillColor(HexColor(WHITE))
    c.setFont("Helvetica-Bold", 5)
    c.drawString(6*mm, CARD_HEIGHT - 12.5*mm, "PREMIUM LOYALTY CARD")


def _draw_pdf_customer_info(c, card):
    c.setFillColor(HexColor(WHITE))
    c.setFont("Helvetica-Bold", 5.5)
    name = card.user.name if card.user else "Customer"
    email = card.user.email if card.user else ""
    c.drawString(6*mm, CARD_HEIGHT - 18*mm, name)
    c.drawString(6*mm, CARD_HEIGHT - 22*mm, email)

    c.setFillColor(HexColor(YELLOW))
    c.setFont("Courier-Bold", 6)
    c.drawString(6*mm, CARD_HEIGHT - 27*mm, card.card_number)


def _draw_pdf_points_section(c, card):
    y = CARD_HEIGHT - 34*mm
    c.setFillColor(HexColor(ORANGE))
    c.setFont("Helvetica-Bold", 4.5)
    c.drawString(6*mm, y, "POINTS BALANCE")
    y -= 5*mm

    pts = [
        ("TOTAL", str(card.total_points), YELLOW),
        ("REMAINING", str(card.remaining_points), WHITE),
    ]
    px = 6*mm
    for label, val, col in pts:
        c.setFillColor(HexColor(col))
        c.setFont("Helvetica-Bold", 6)
        c.drawString(px, y, val)
        c.setFillColor(HexColor(GRAY))
        c.setFont("Helvetica", 3.5)
        c.drawString(px, y - 2.5*mm, label)
        px += 20*mm


def _draw_pdf_qr_section(c, card, request=None):
    qr_pil = _get_qr_pil_image(card, request)
    qr_size = PDF_QR_SIZE_MM * mm
    qr_x = CARD_WIDTH - qr_size - 5*mm
    qr_y = (CARD_HEIGHT - qr_size) / 2

    c.setFillColor(HexColor(WHITE))
    c.roundRect(qr_x - 0.5*mm, qr_y - 0.5*mm, qr_size + 1*mm, qr_size + 1*mm, 1*mm, fill=1, stroke=0)

    qr_path = BytesIO()
    qr_pil.save(qr_path, format="PNG")
    qr_path.seek(0)
    c.drawImage(ImageReader(qr_path), qr_x, qr_y, width=qr_size, height=qr_size)

    c.setFillColor(HexColor(DIM))
    c.setFont("Helvetica", 3)
    c.drawString(qr_x, qr_y - 2*mm, timezone.now().strftime("%d-%m-%Y"))


def generate_loyalty_card_image(card, request=None):
    cw = int(CARD_WIDTH)
    ch = int(CARD_HEIGHT)
    img = Image.new("RGB", (cw, ch))
    draw = ImageDraw.Draw(img)

    _draw_gradient_background_pil(draw, cw, ch, BLACK_TOP, BLACK_BOT)
    draw.rounded_rectangle([6, 6, cw - 6, ch - 6], radius=12, outline=ORANGE, width=2)
    draw.rounded_rectangle([8, 8, cw - 8, ch - 8], radius=10, outline=YELLOW, width=1)

    try:
        title_font = ImageFont.truetype("arial.ttf", 14)
        subtitle_font = ImageFont.truetype("arial.ttf", 9)
        cardno_font = ImageFont.truetype("arial.ttf", 11)
        customer_font = ImageFont.truetype("arial.ttf", 10)
        email_font = ImageFont.truetype("arial.ttf", 8)
        label_font = ImageFont.truetype("arial.ttf", 6)
        value_font = ImageFont.truetype("arial.ttf", 10)
        small_font = ImageFont.truetype("arial.ttf", 5)
        points_label_font = ImageFont.truetype("arial.ttf", 8)
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        cardno_font = ImageFont.load_default()
        customer_font = ImageFont.load_default()
        email_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        points_label_font = ImageFont.load_default()

    draw.text((14, 10), "LOGO", fill=ORANGE, font=title_font)
    draw.text((14, 26), "PREMIUM LOYALTY CARD", fill=WHITE, font=subtitle_font)

    name = card.user.name if card.user else "Customer"
    email = card.user.email if card.user else ""
    draw.text((14, 42), name, fill=WHITE, font=customer_font)
    draw.text((14, 54), email, fill=GRAY, font=email_font)

    draw.text((14, 68), card.card_number, fill=YELLOW, font=cardno_font)

    y = 84
    draw.text((14, y), "POINTS BALANCE", fill=ORANGE, font=points_label_font)
    y += 14

    pts = [
        ("TOTAL", str(card.total_points), YELLOW),
        ("REMAINING", str(card.remaining_points), WHITE),
    ]
    px = 14
    for label, val, col in pts:
        draw.text((px, y), val, fill=col, font=value_font)
        draw.text((px, y + 12), label, fill=GRAY, font=small_font)
        px += 36

    qr_pil = _get_qr_pil_image(card, request)
    qr_resized = qr_pil.resize((PNG_QR_SIZE, PNG_QR_SIZE), Image.LANCZOS)
    qr_x = cw - PNG_QR_SIZE - 14
    qr_y = int((ch - PNG_QR_SIZE) / 2)

    white_bg = Image.new("RGB", (PNG_QR_SIZE + 8, PNG_QR_SIZE + 8), "white")
    white_bg.paste(qr_resized, (4, 4))
    img.paste(white_bg, (qr_x - 4, qr_y - 4))

    draw.text((qr_x, qr_y + PNG_QR_SIZE + 4), timezone.now().strftime("%d-%m-%Y"), fill=DIM, font=small_font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    filename = f"loyalty_card_{card.card_number}.png"
    card.card_image.save(filename, ContentFile(buf.getvalue()), save=False)
    card.save(update_fields=['card_image'])
    return card
