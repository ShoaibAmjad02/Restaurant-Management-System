import json
import qrcode
from io import BytesIO
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


def generate_qr_code_image(card):
    qr_data = json.dumps(card.generate_qr_data())
    qr = qrcode.make(qr_data, box_size=10)
    qr = qr.convert("RGB")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)

    filename = f"qr_{card.card_number}.png"
    card.qr_code_image.save(filename, ContentFile(buf.getvalue()), save=False)
    card.save(update_fields=['qr_code_image'])
    return card


def _get_qr_pil_image(card):
    if card.qr_code_image and card.qr_code_image.storage.exists(card.qr_code_image.name):
        try:
            card.qr_code_image.open('rb')
            return Image.open(card.qr_code_image)
        except Exception:
            pass
    generate_qr_code_image(card)
    if card.qr_code_image and card.qr_code_image.storage.exists(card.qr_code_image.name):
        try:
            card.qr_code_image.open('rb')
            return Image.open(card.qr_code_image)
        except Exception:
            pass
    data = json.dumps(card.generate_qr_data())
    qr = qrcode.make(data, box_size=6)
    return qr.convert("RGB")


def _draw_card_border(c, w, h):
    c.setStrokeColor(HexColor(ORANGE))
    c.setLineWidth(0.5)
    c.roundRect(3*mm, 3*mm, w - 6*mm, h - 6*mm, 4*mm, fill=0, stroke=1)
    c.setStrokeColor(HexColor(YELLOW))
    c.setLineWidth(0.2)
    c.roundRect(3.5*mm, 3.5*mm, w - 7*mm, h - 7*mm, 3.5*mm, fill=0, stroke=1)


def generate_loyalty_card_pdf(card):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(CARD_WIDTH, CARD_HEIGHT))

    _draw_gradient_background_pdf(c, CARD_WIDTH, CARD_HEIGHT, BLACK_TOP, BLACK_BOT)
    _draw_card_border(c, CARD_WIDTH, CARD_HEIGHT)

    _draw_pdf_logo_section(c)
    _draw_pdf_customer_info(c, card)
    _draw_pdf_points_section(c, card)
    _draw_pdf_qr_section(c, card)

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


def _draw_pdf_qr_section(c, card):
    qr_pil = _get_qr_pil_image(card)
    qr_path = BytesIO()
    qr_pil.save(qr_path, format="PNG")
    qr_path.seek(0)
    qr_x = CARD_WIDTH - 18*mm
    qr_y = 8*mm
    c.drawImage(ImageReader(qr_path), qr_x, qr_y, width=13*mm, height=13*mm)

    c.setFillColor(HexColor(DIM))
    c.setFont("Helvetica", 3)
    c.drawString(qr_x, 6*mm, timezone.now().strftime("%d-%m-%Y"))


def generate_loyalty_card_image(card):
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

    qr_pil = _get_qr_pil_image(card)
    qr_resized = qr_pil.resize((42, 42))
    qr_x = cw - 52
    qr_y = 10
    img.paste(qr_resized, (qr_x, qr_y))

    draw.text((qr_x, 54), timezone.now().strftime("%d-%m-%Y"), fill=DIM, font=small_font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    filename = f"loyalty_card_{card.card_number}.png"
    card.card_image.save(filename, ContentFile(buf.getvalue()), save=False)
    card.save(update_fields=['card_image'])
    return card
