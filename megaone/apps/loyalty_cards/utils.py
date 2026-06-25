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


def _lerp_color(c1, c2, t):
    """Linearly interpolate between two hex colors."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _draw_gradient_background_pdf(c, w, h, color1, color2):
    """Draw a vertical gradient background on a ReportLab canvas."""
    steps = 60
    for i in range(steps):
        t = i / steps
        color_hex = _lerp_color(color1, color2, t)
        c.setFillColor(HexColor(color_hex))
        strip_h = h / steps
        c.rect(0, i * strip_h, w, strip_h + 0.5, fill=1, stroke=0)


def _draw_gradient_background_pil(draw, w, h, color1, color2):
    """Draw a vertical gradient background on a PIL ImageDraw."""
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


def generate_loyalty_card_pdf(card):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(CARD_WIDTH, CARD_HEIGHT))

    GRADIENT_TOP = "#7c3aed"
    GRADIENT_BOT = "#1e3a8a"
    GOLD = "#f59e0b"
    WHITE_HEX = "#ffffff"
    LIGHT_HEX = "#cbd5e1"
    DIM_HEX = "#94a3b8"

    _draw_gradient_background_pdf(c, CARD_WIDTH, CARD_HEIGHT, GRADIENT_TOP, GRADIENT_BOT)

    c.setStrokeColor(HexColor("#ffffff"))
    c.setLineWidth(0.3)
    c.roundRect(3*mm, 3*mm, CARD_WIDTH - 6*mm, CARD_HEIGHT - 6*mm, 4*mm, fill=0, stroke=1)

    c.setFillColor(HexColor(GOLD))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(8*mm, CARD_HEIGHT - 10*mm, "RESTAURANT")

    c.setFillColor(HexColor(WHITE_HEX))
    c.setFont("Helvetica-Bold", 6)
    c.drawString(8*mm, CARD_HEIGHT - 15*mm, "PREMIUM LOYALTY CARD")

    c.setFillColor(HexColor(GOLD))
    c.setFont("Courier-Bold", 7)
    c.drawString(8*mm, CARD_HEIGHT - 20*mm, card.card_number)

    y = CARD_HEIGHT - 27*mm
    c.setFillColor(HexColor(LIGHT_HEX))
    c.setFont("Helvetica", 5)
    lines = [
        (card.user.name if card.user else "Customer", None),
        (card.user.email if card.user else "", None),
    ]
    for val, _ in lines:
        c.drawString(8*mm, y, val)
        y -= 3.5*mm

    c.setFillColor(HexColor(GOLD))
    c.setFont("Helvetica", 4)
    c.drawString(8*mm, y - 1*mm, "Points Summary")
    y -= 5*mm

    pts_data = [
        ("Total", str(card.total_points), WHITE_HEX),
        ("Used", str(card.used_points), "#f87171"),
        ("Remaining", str(card.remaining_points), "#4ade80"),
    ]
    px = 8*mm
    for label, val, col in pts_data:
        c.setFillColor(HexColor(col))
        c.setFont("Helvetica-Bold", 6)
        c.drawString(px, y, val)
        c.setFillColor(HexColor(DIM_HEX))
        c.setFont("Helvetica", 4)
        c.drawString(px, y - 2.5*mm, label)
        px += 15*mm

    qr_pil = _get_qr_pil_image(card)
    qr_path = BytesIO()
    qr_pil.save(qr_path, format="PNG")
    qr_path.seek(0)
    c.drawImage(ImageReader(qr_path), CARD_WIDTH - 20*mm, 8*mm, width=14*mm, height=14*mm)

    c.setFillColor(HexColor(DIM_HEX))
    c.setFont("Helvetica", 3.5)
    c.drawString(CARD_WIDTH - 20*mm, 6*mm, timezone.now().strftime("%d-%m-%Y"))

    c.save()
    buffer.seek(0)

    filename = f"loyalty_card_{card.card_number}.pdf"
    card.card_pdf.save(filename, ContentFile(buffer.getvalue()), save=False)
    card.save(update_fields=['card_pdf'])
    return card


def generate_loyalty_card_image(card):
    GRADIENT_TOP = "#7c3aed"
    GRADIENT_BOT = "#1e3a8a"

    cw = int(CARD_WIDTH)
    ch = int(CARD_HEIGHT)
    img = Image.new("RGB", (cw, ch))
    draw = ImageDraw.Draw(img)

    _draw_gradient_background_pil(draw, cw, ch, GRADIENT_TOP, GRADIENT_BOT)

    draw.rounded_rectangle([6, 6, cw - 6, ch - 6], radius=12, outline="white", width=1)

    try:
        title_font = ImageFont.truetype("arial.ttf", 18)
        subtitle_font = ImageFont.truetype("arial.ttf", 11)
        cardno_font = ImageFont.truetype("arial.ttf", 13)
        label_font = ImageFont.truetype("arial.ttf", 9)
        value_font = ImageFont.truetype("arial.ttf", 10)
        small_font = ImageFont.truetype("arial.ttf", 7)
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        cardno_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.text((16, 14), "RESTAURANT", fill="#f59e0b", font=title_font)
    draw.text((16, 34), "PREMIUM LOYALTY CARD", fill="white", font=subtitle_font)

    card_no = card.card_number
    draw.text((16, 52), card_no, fill="#f59e0b", font=cardno_font)

    y = 74
    draw.text((16, y), card.user.name if card.user else "Customer", fill="#cbd5e1", font=label_font)
    y += 14
    draw.text((16, y), card.user.email if card.user else "", fill="#cbd5e1", font=label_font)
    y += 18

    draw.text((16, y), "Points Summary", fill="#f59e0b", font=subtitle_font)
    y += 16

    pts = [
        ("Total", str(card.total_points), "#ffffff"),
        ("Used", str(card.used_points), "#f87171"),
        ("Remaining", str(card.remaining_points), "#4ade80"),
    ]
    px = 16
    for label, val, col in pts:
        draw.text((px, y), val, fill=col, font=value_font)
        draw.text((px, y + 12), label, fill="#94a3b8", font=small_font)
        px += 40

    qr_pil = _get_qr_pil_image(card)
    qr_resized = qr_pil.resize((48, 48))
    qr_x = cw - 60
    qr_y = 14
    img.paste(qr_resized, (qr_x, qr_y))

    draw.text((cw - 60, 64), timezone.now().strftime("%d-%m-%Y"), fill="#94a3b8", font=small_font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    filename = f"loyalty_card_{card.card_number}.png"
    card.card_image.save(filename, ContentFile(buf.getvalue()), save=False)
    card.save(update_fields=['card_image'])
    return card
