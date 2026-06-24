import io
import json
import pathlib
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont


CARD_WIDTH = 86 * mm
CARD_HEIGHT = 54 * mm


def generate_qr_code_image(card):
    """Generate a standalone QR code image and save it to the card."""
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
    """Return a PIL Image of the QR code, generating it if needed."""
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

    DARK = HexColor("#1a1a2e")
    GOLD = HexColor("#f59e0b")
    ACCENT = HexColor("#e2e8f0")

    c.setFillColor(DARK)
    c.rect(0, 0, CARD_WIDTH, CARD_HEIGHT, fill=1, stroke=0)

    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(6*mm, CARD_HEIGHT - 8*mm, "RESTAURANT")

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 5)
    c.drawString(6*mm, CARD_HEIGHT - 13*mm, "LOYALTY CARD")

    y = CARD_HEIGHT - 20*mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica", 5)
    lines = [
        ("Name", card.user.name if card.user else "Customer"),
        ("Email", card.user.email if card.user else ""),
        ("Card #", card.card_number),
        ("Total Points", str(card.total_points)),
        ("Used Points", str(card.used_points)),
        ("Remaining", str(card.remaining_points)),
        ("Issue Date", timezone.now().strftime("%d-%m-%Y")),
    ]
    for label, val in lines:
        c.drawString(6*mm, y, f"{label}: {val}")
        y -= 3.5*mm

    # Embed QR image directly from saved file or generate
    qr_pil = _get_qr_pil_image(card)
    qr_path = BytesIO()
    qr_pil.save(qr_path, format="PNG")
    qr_path.seek(0)
    c.drawImage(ImageReader(qr_path), CARD_WIDTH - 22*mm, 6*mm, width=16*mm, height=16*mm)

    c.save()
    buffer.seek(0)

    filename = f"loyalty_card_{card.card_number}.pdf"
    card.card_pdf.save(filename, ContentFile(buffer.getvalue()), save=False)
    card.save(update_fields=['card_pdf'])
    return card


def generate_loyalty_card_image(card):
    img = Image.new("RGB", (int(CARD_WIDTH), int(CARD_HEIGHT)), "#1a1a2e")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 14)
        label_font = ImageFont.truetype("arial.ttf", 9)
        value_font = ImageFont.truetype("arial.ttf", 10)
    except Exception:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()

    draw.text((12, 8), "RESTAURANT", fill="#f59e0b", font=title_font)
    draw.text((12, 28), "LOYALTY CARD", fill="white", font=label_font)

    y = 50
    info = [
        ("Name", card.user.name if card.user else "Customer"),
        ("Email", card.user.email if card.user else ""),
        ("Card #", card.card_number),
        ("Total Points", str(card.total_points)),
        ("Used Points", str(card.used_points)),
        ("Remaining", str(card.remaining_points)),
        ("Date", timezone.now().strftime("%d-%m-%Y")),
    ]
    for label, val in info:
        draw.text((12, y), f"{label}:", fill="#94a3b8", font=label_font)
        draw.text((65, y), val, fill="white", font=value_font)
        y += 14

    # Paste QR image onto card canvas
    qr_pil = _get_qr_pil_image(card)
    qr_resized = qr_pil.resize((48, 48))
    qr_x = int(CARD_WIDTH) - 56
    qr_y = 8
    img.paste(qr_resized, (qr_x, qr_y))

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    filename = f"loyalty_card_{card.card_number}.png"
    card.card_image.save(filename, ContentFile(buf.getvalue()), save=False)
    card.save(update_fields=['card_image'])
    return card
