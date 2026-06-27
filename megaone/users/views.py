import io
import json
import uuid
import subprocess
import traceback
import qrcode
from django.http import HttpResponse, JsonResponse, FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet, Sum, Q, Count
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, UpdateView, RedirectView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.utils.dateformat import DateFormat
from datetime import datetime, timedelta, timezone as dt_timezone

from menu.models import Food, Category
from .models import User, Invoice, InvoiceItem, KitchenOrder, KitchenOrderItem, RestaurantTable, LoyaltyCard, LoyaltyTransaction, QRTableOffer, TimeBasedOffer, TodayDeal
from .loyalty_utils import generate_qr_code_image, generate_loyalty_card_pdf, generate_loyalty_card_image

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

User = get_user_model()


# =========================
# BASE
# =========================
class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    pk_url_kwarg = "pk"

user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Updated successfully")

    def get_success_url(self) -> str:
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        return self.request.user

user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})

user_redirect_view = UserRedirectView.as_view()


# =========================
# AUTH
# =========================
def register_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("food-delivery:food_delivery_registration")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("food-delivery:food_delivery_registration")

        User.objects.create_user(email=email, password=password1, name=name)
        messages.success(request, "Registration successful.")
        return redirect("food-delivery:food_delivery_login")

    return redirect("food-delivery:food_delivery_registration")


def food_delivery_login(request):
    next_url = request.GET.get("next") or request.POST.get("next") or ""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            if next_url:
                return redirect(next_url)
            # Auto-create loyalty card for online registered customers only
            if not user.is_staff and not getattr(user, "is_kitchen", False) and not user.is_superuser:
                from .loyalty_utils import generate_qr_code_image, generate_loyalty_card_pdf, generate_loyalty_card_image
                card, created = LoyaltyCard.objects.get_or_create(
                    user=user,
                    defaults={'status': 'ACTIVE'}
                )
                if created or not card.qr_code_image or not card.card_pdf:
                    try:
                        generate_qr_code_image(card, request)
                        generate_loyalty_card_pdf(card, request)
                        generate_loyalty_card_image(card, request)
                    except Exception:
                        pass
                # First-time redirect to loyalty card page (using DB flag)
                if not card.first_card_popup_shown:
                    return redirect("users:loyalty_card_view")
            if user.is_staff:
                return redirect("users:admin_dashboard")
            elif getattr(user, "is_kitchen", False):
                return redirect("users:kitchen_dashboard")
            return redirect("/")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("food-delivery:food_delivery_login")

    return render(request, "food-delivery/login.html")


def logout_view(request):
    logout(request)
    return redirect("/")


# =========================
# QR MENU ACCESS
# =========================
@csrf_exempt
def qr_menu_view(request):
    table_no = request.GET.get("table")
    token = request.GET.get("token")

    # Check session first for returning customers
    session_table = request.session.get("table_no")
    session_token = request.session.get("table_token")

    if table_no and token:
        try:
            table = RestaurantTable.objects.get(table_no=table_no, qr_token=token)
            request.session["table_no"] = table.table_no
            request.session["table_token"] = token
            if not request.session.get("customer_session_id"):
                request.session["customer_session_id"] = str(uuid.uuid4())
        except RestaurantTable.DoesNotExist:
            return render(request, "food-delivery/qr_error.html", {"error": "Invalid or expired QR code."})
    elif session_table and session_token:
        try:
            table = RestaurantTable.objects.get(table_no=session_table, qr_token=session_token)
        except RestaurantTable.DoesNotExist:
            return render(request, "food-delivery/qr_error.html", {"error": "Session expired. Please scan QR again."})
    else:
        return render(request, "food-delivery/qr_error.html", {"error": "Invalid QR code link."})

    products = Food.objects.filter(available=1)

    return render(request, "food-delivery/restaurant-detail.html", {
        "products": products,
        "table_no": table.table_no,
        "is_qr_customer": True,
    })


@login_required(login_url='food-delivery:food_delivery_login')
def food_delivery_restaurant_detail(request):
    products = Food.objects.filter(available=1)
    return render(request, 'food-delivery/restaurant-detail.html', {
        "products": products,
        "table_no": request.session.get("table_no"),
    })


# =========================
# CHECKOUT
# =========================
def _create_order_from_cart(cart, request, user=None, payment_method="card",
                            customer_timezone="UTC", use_loyalty_points=None,
                            secondary_payment_method=None):
    table_no = request.session.get("table_no")
    customer_session = request.session.get("customer_session_id") or str(uuid.uuid4())

    subtotal_amount = 0
    for item in cart:
        qty = int(item["qty"])
        price = float(item["price"])
        subtotal_amount += qty * price

    # ---------- Today's Deal Discount ----------
    deal_obj = None
    deal_discount_amt = 0
    deal_id = request.session.pop("deal_checkout_id", None) if request else None
    if deal_id:
        try:
            deal_obj = TodayDeal.objects.get(id=deal_id, is_active=True)
            deal_products = list(deal_obj.products.all())
            if deal_obj.free_product:
                deal_products.append(deal_obj.free_product)
            original_total = sum(float(p.price) for p in deal_products)
            if deal_obj.combo_price and original_total > 0:
                deal_discount_amt = original_total - float(deal_obj.combo_price)
                if deal_discount_amt < 0:
                    deal_discount_amt = 0
        except TodayDeal.DoesNotExist:
            pass
        request.session.pop("deal_checkout_cart", None)

    # ---------- Offer Discount ----------
    qr_offer_discount_pct = 0
    qr_offer_discount_amt = 0

    if payment_method != "loyalty" and not deal_obj:
        time_offer = TimeBasedOffer.objects.filter(is_active=True).first()
        if time_offer:
            qr_offer_discount_pct = float(time_offer.discount_percentage)
            qr_offer_discount_amt = round(subtotal_amount * qr_offer_discount_pct / 100, 2)
        else:
            is_qr_table_order = table_no is not None and user is None
            if is_qr_table_order:
                qr_offer = QRTableOffer.objects.first()
                if qr_offer:
                    qr_offer.check_and_update_status()
                    if qr_offer.is_active:
                        qr_offer_discount_pct = float(qr_offer.discount_percentage)
                        qr_offer_discount_amt = round(subtotal_amount * qr_offer_discount_pct / 100, 2)

    # For deals, use deal discount in place of offer discount
    if deal_obj and deal_discount_amt > 0:
        qr_offer_discount_amt = deal_discount_amt

    # ---------- Loyalty ----------
    is_loyalty = payment_method == "loyalty"
    loyalty_points_used = 0
    loyalty_card = None
    remaining_amount = subtotal_amount - qr_offer_discount_amt
    if remaining_amount < 0:
        remaining_amount = 0
    if is_loyalty and user:
        try:
            loyalty_card = LoyaltyCard.objects.get(user=user, status='ACTIVE')
            available = int(loyalty_card.remaining_points)
            requested = int(use_loyalty_points) if use_loyalty_points else available
            loyalty_points_used = max(0, min(requested, available, int(remaining_amount)))
            remaining_amount = remaining_amount - loyalty_points_used
            if remaining_amount < 0:
                remaining_amount = 0
        except LoyaltyCard.DoesNotExist:
            is_loyalty = False
            payment_method = secondary_payment_method or "card"

    if is_loyalty and remaining_amount > 0 and secondary_payment_method:
        store_method = f"loyalty+{secondary_payment_method}"
        tax_pct = 5 if secondary_payment_method == "card" else 18
    elif is_loyalty and remaining_amount <= 0:
        store_method = "loyalty"
        tax_pct = 0
    else:
        store_method = payment_method
        tax_pct = 5 if payment_method == "card" else 18

    tax_amount = round(remaining_amount * tax_pct / 100, 2)
    grand_total = remaining_amount + tax_amount
    if grand_total < 0:
        grand_total = 0

    invoice = Invoice.objects.create(
        user=user,
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        payment_method=store_method,
        customer_timezone=customer_timezone,
        tax_percentage=tax_pct,
        tax_amount=tax_amount,
        subtotal_amount=subtotal_amount,
        total_amount=grand_total,
        table_no=table_no,
        customer_session_id=customer_session,
        is_loyalty_payment=is_loyalty,
        loyalty_points_used=loyalty_points_used,
        qr_offer_discount_percentage=qr_offer_discount_pct,
        qr_offer_discount_amount=qr_offer_discount_amt,
        deal=deal_obj,
        deal_discount_amount=deal_discount_amt,
    )

    for item in cart:
        qty = int(item["qty"])
        price = float(item["price"])
        subtotal = qty * price
        InvoiceItem.objects.create(
            invoice=invoice, product_name=item["name"],
            price=price, quantity=qty, subtotal=subtotal,
        )

    order = KitchenOrder.objects.create(
        invoice=invoice, order_number="", table_no=table_no,
        created_at=timezone.now(),
    )
    order.order_number = f"ORD-{order.id}"
    order.save()

    if loyalty_card and loyalty_points_used > 0:
        try:
            loyalty_card.redeem_points(loyalty_points_used, order_number=order.order_number)
        except ValueError:
            pass

    for item in cart:
        KitchenOrderItem.objects.create(
            order=order, product_name=item["name"], quantity=int(item["qty"]),
        )

    invoice.generate_qr_code(request)
    invoice.save()

    return invoice


@csrf_exempt
def guest_checkout(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        cart = data.get("cart", [])
        payment_method = data.get("payment_method", "card")
        customer_timezone = data.get("timezone", "UTC")
        use_loyalty_points = data.get("use_loyalty_points")
        secondary_payment_method = data.get("secondary_payment_method")
        if not cart:
            return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

        invoice = _create_order_from_cart(
            cart, request,
            payment_method=payment_method,
            customer_timezone=customer_timezone,
            use_loyalty_points=use_loyalty_points,
            secondary_payment_method=secondary_payment_method,
        )
        return JsonResponse({
            "success": True,
            "invoice_no": invoice.invoice_number,
            "uuid_token": invoice.uuid_token,
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_POST
def checkout_invoice(request):
    try:
        data = json.loads(request.body)
        cart = data.get("cart", [])
        payment_method = data.get("payment_method", "card")
        customer_timezone = data.get("timezone", "UTC")
        use_loyalty_points = data.get("use_loyalty_points")
        secondary_payment_method = data.get("secondary_payment_method")
        if not cart:
            return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

        invoice = _create_order_from_cart(
            cart, request,
            user=request.user,
            payment_method=payment_method,
            customer_timezone=customer_timezone,
            use_loyalty_points=use_loyalty_points,
            secondary_payment_method=secondary_payment_method,
        )
        return JsonResponse({
            "success": True,
            "invoice_no": invoice.invoice_number,
            "uuid_token": invoice.uuid_token,
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# =========================
# ORDER TRACKING
# =========================
def order_tracking(request, invoice_no):
    try:
        invoice = Invoice.objects.get(invoice_number=invoice_no)
        order = invoice.kitchen_order
    except (Invoice.DoesNotExist, KitchenOrder.DoesNotExist):
        return render(request, "food-delivery/order_tracking.html", {"error": "Order not found"})

    items = InvoiceItem.objects.filter(invoice=invoice)

    invoice_date = timezone.localtime(invoice.created_at).strftime("%d-%m-%Y %I:%M:%S %p")
    invoice_time = timezone.localtime(invoice.created_at).strftime("%I:%M:%S %p")

    return render(request, "food-delivery/order_tracking.html", {
        "invoice": invoice,
        "order": order,
        "items": items,
        "table_no": invoice.table_no,
        "invoice_date": invoice_date,
        "invoice_time": invoice_time,
    })


def order_tracking_data(request, invoice_no):
    try:
        invoice = Invoice.objects.get(invoice_number=invoice_no)
        order = invoice.kitchen_order
    except (Invoice.DoesNotExist, KitchenOrder.DoesNotExist):
        return JsonResponse({"error": "Not found"}, status=404)

    return JsonResponse({
        "invoice_no": invoice.invoice_number,
        "uuid_token": invoice.uuid_token,
        "table_no": invoice.table_no,
        "status": order.status,
        "total_amount": float(invoice.total_amount),
        "created_at": timezone.localtime(invoice.created_at).strftime("%d-%m-%Y %I:%M:%S %p"),
        "pdf_url": f"/users/invoice/{invoice.uuid_token}/",
    })


# =========================
# SECURE INVOICE VIEW -> Redirect to PDF
# =========================
def secure_invoice_view(request, uuid_token):
    return redirect("users:invoice_pdf", uuid_token=uuid_token)


# =========================
# SET TIMEZONE
# =========================
@csrf_exempt
def set_timezone(request):
    if request.method == "POST":
        data = json.loads(request.body)
        tz = data.get("timezone", "")
        if tz:
            request.session["user_timezone"] = tz
            if request.user.is_authenticated:
                request.user.timezone = tz
                request.user.save(update_fields=["timezone"])
            return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


# =========================
# INVOICE DETAIL (legacy redirect)
# =========================
def invoice_detail(request, invoice_no):
    try:
        invoice = Invoice.objects.get(invoice_number=invoice_no)
        return redirect("users:invoice_pdf", uuid_token=invoice.uuid_token)
    except Invoice.DoesNotExist:
        return HttpResponse("Invoice not found", status=404)


# =========================
# INVOICE PDF
# =========================
def _generate_invoice_qr_image(invoice, request=None):
    domain = "http://localhost:8000"
    if request:
        domain = f"{request.scheme}://{request.get_host()}"
    secure_url = f"{domain}/users/invoice/{invoice.uuid_token}/verify/"
    qr = qrcode.make(secure_url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def invoice_pdf(request, uuid_token):
    invoice = Invoice.objects.filter(uuid_token=uuid_token).first()

    if not invoice:
        return HttpResponse("Invoice not found", status=404)

    order = getattr(invoice, "kitchen_order", None)

    status = order.status if order else "pending"
    order_no = order.order_number if order else "N/A"

    items = list(invoice.items.all())

    # ==========================
    # DYNAMIC THERMAL HEIGHT (60mm)
    # ==========================

    width = 60 * mm

    loyalty_height = 0
    if invoice.user:
        if LoyaltyCard.objects.filter(user=invoice.user).exists():
            loyalty_height = 45 * mm

    header_height = 65 * mm
    item_per_height = 9 * mm
    summary_height = 50 * mm
    qr_height = 40 * mm
    footer_height = 15 * mm

    height = (
        header_height
        + (len(items) * item_per_height)
        + summary_height
        + qr_height
        + footer_height
        + loyalty_height
    )

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    pdf.setTitle(invoice.invoice_number)

    w, h = width, height

    DARK = HexColor("#111827")
    GRAY = HexColor("#6b7280")
    GREEN = HexColor("#16a34a")

    MARGIN = 4 * mm
    right = w - MARGIN

    # ==========================
    # HEADER
    # ==========================
    y = h - 8 * mm

    pdf.setFillColor(DARK)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(w / 2, y, "RESTAURANT")

    y -= 5 * mm
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(w / 2, y, "Food Street Restaurant")

    y -= 4 * mm
    pdf.drawCentredString(w / 2, y, "+92 XXX XXXXXXX")

    y -= 5 * mm
    pdf.setStrokeColor(DARK)
    pdf.line(MARGIN, y, right, y)

    # ==========================
    # CUSTOMER INFO
    # ==========================
    y -= 6 * mm
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(DARK)

    if invoice.user:
        customer_name = invoice.user.name or invoice.user.email
        customer_email = invoice.user.email
    else:
        customer_name = "Walk-in Customer"
        customer_email = "--------"

    customer_lines = [
        ("Customer Name", customer_name),
        ("Customer Email", customer_email),
    ]
    for label, val in customer_lines:
        pdf.drawString(MARGIN, y, f"{label}")
        pdf.drawRightString(right, y, val)
        y -= 4 * mm

    pdf.line(MARGIN, y, right, y)
    y -= 5 * mm

    # ==========================
    # INVOICE INFO
    # ==========================
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(DARK)

    info_lines = [
        ("Invoice #", invoice.invoice_number),
        ("Order #", order_no),
        ("Table #", str(invoice.table_no or "N/A")),
        ("Date", timezone.localtime(invoice.created_at).strftime("%d-%m-%Y %I:%M:%S %p")),
    ]
    for label, val in info_lines:
        pdf.drawString(MARGIN, y, f"{label}")
        pdf.drawRightString(right, y, val)
        y -= 4 * mm

    pdf.line(MARGIN, y, right, y)

    # ==========================
    # PAYMENT INFO
    # ==========================
    y -= 5 * mm
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(DARK)
    pay_method = invoice.payment_method or "N/A"
    tax_pct = float(invoice.tax_percentage) if invoice.tax_percentage else 0
    pay_lines = [
        ("Payment Method", pay_method.upper()),
        ("Tax Percentage", f"{tax_pct:.0f}%"),
    ]
    for label, val in pay_lines:
        pdf.drawString(MARGIN, y, f"{label}")
        pdf.drawRightString(right, y, val)
        y -= 4 * mm

    pdf.line(MARGIN, y, right, y)

    # ==========================
    # ITEMS
    # ==========================
    y -= 5 * mm
    subtotal = 0

    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawString(MARGIN, y, "ITEM")
    pdf.drawRightString(right, y, "TOTAL")
    y -= 4 * mm

    pdf.setFont("Helvetica", 7)
    for item in items:
        subtotal += float(item.subtotal)
        name = item.product_name[:22]
        pdf.drawString(MARGIN, y, name)
        pdf.drawRightString(right, y, f"Rs {float(item.subtotal):.0f}")
        y -= 4 * mm
        pdf.setFont("Helvetica", 6)
        pdf.setFillColor(GRAY)
        pdf.drawString(MARGIN, y, f"{item.quantity} x Rs {float(item.price):.0f}")
        pdf.setFillColor(DARK)
        pdf.setFont("Helvetica", 7)
        y -= 5 * mm

    pdf.line(MARGIN, y, right, y)

    # ==========================
    # SUMMARY
    # ==========================
    y -= 6 * mm
    tax_amount = float(invoice.tax_amount) if invoice.tax_amount else round(subtotal * 0.05, 2)
    grand_total = float(invoice.total_amount)
    sub_amt = float(invoice.subtotal_amount) if invoice.subtotal_amount else subtotal
    qr_disc_pct = float(invoice.qr_offer_discount_percentage) if invoice.qr_offer_discount_percentage else 0
    qr_disc_amt = float(invoice.qr_offer_discount_amount) if invoice.qr_offer_discount_amount else 0

    pdf.setFont("Helvetica", 8)
    pdf.drawString(MARGIN, y, "Subtotal")
    pdf.drawRightString(right, y, f"Rs {sub_amt:.0f}")
    y -= 5 * mm

    deal_disc_amt = float(invoice.deal_discount_amount) if invoice.deal_discount_amount else 0
    if deal_disc_amt > 0:
        pdf.setFont("Helvetica", 7)
        pdf.setFillColor(HexColor("#8b5cf6"))
        pdf.drawString(MARGIN, y, f"Deal Discount")
        pdf.drawRightString(right, y, f"-Rs {deal_disc_amt:.0f}")
        y -= 5 * mm
    elif qr_disc_pct > 0 and qr_disc_amt > 0:
        pdf.setFont("Helvetica", 7)
        pdf.setFillColor(HexColor("#f59e0b"))
        pdf.drawString(MARGIN, y, f"Discount ({qr_disc_pct:.0f}%)")
        pdf.drawRightString(right, y, f"-Rs {qr_disc_amt:.0f}")
        y -= 5 * mm

    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(GRAY)
    pdf.drawString(MARGIN, y, f"Tax ({tax_pct:.0f}%)")
    pdf.drawRightString(right, y, f"Rs {tax_amount:.0f}")
    y -= 5 * mm
    pdf.setFillColor(DARK)

    pdf.line(MARGIN, y, right, y)
    y -= 6 * mm

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(MARGIN, y, "GRAND TOTAL")
    pdf.drawRightString(right, y, f"Rs {grand_total:.0f}")

    y -= 8 * mm

    pdf.setFont("Helvetica-Bold", 8)
    pdf.setFillColor(GREEN)
    pdf.drawCentredString(w / 2, y, f"STATUS : {status.upper()}")
    pdf.setFillColor(DARK)

    # ==========================
    # LOYALTY CARD INFO (Order Total → Loyalty Used → Paid By Cash → Remaining Balance)
    # ==========================
    if invoice.user:
        lcard = LoyaltyCard.objects.filter(user=invoice.user).first()
        if lcard:
            y -= 5 * mm
            pdf.setFont("Helvetica-Bold", 7)
            pdf.setFillColor(HexColor("#f59e0b"))
            pdf.drawCentredString(w / 2, y, "LOYALTY CARD")
            pdf.setFillColor(DARK)
            y -= 4 * mm
            pdf.setFont("Helvetica", 6)

            pay_method = invoice.payment_method or ""
            is_hybrid = pay_method.startswith("loyalty+")
            secondary_label = pay_method.split("+")[1].upper() if is_hybrid else "CASH"

            total_for_display = float(invoice.subtotal_amount) if invoice.subtotal_amount else 0
            pts_used = int(invoice.loyalty_points_used) if invoice.loyalty_points_used else 0
            remaining_amt = float(invoice.total_amount) if invoice.total_amount else 0

            display_lines = [
                ("Order Total", f"Rs {total_for_display:.0f}"),
            ]
            if pts_used > 0:
                display_lines.append(("Loyalty Used", f"-Rs {pts_used}"))
                display_lines.append((f"Paid By {secondary_label}", f"Rs {remaining_amt:.0f}"))
            display_lines.append(("Card #", lcard.card_number))
            display_lines.append(("Remaining Balance", f"{lcard.remaining_points} pts"))

            for label, val in display_lines:
                pdf.drawString(MARGIN, y, label)
                pdf.drawRightString(right, y, val)
                y -= 3.5 * mm

            if invoice.loyalty_points_earned and invoice.loyalty_points_earned > 0:
                pdf.setFillColor(HexColor("#16a34a"))
                pdf.drawString(MARGIN, y, "Earned This Order")
                pdf.drawRightString(right, y, f"+{invoice.loyalty_points_earned} pts")
                pdf.setFillColor(DARK)
                y -= 3.5 * mm

            y -= 2 * mm
            pdf.line(MARGIN, y, right, y)
            y -= 4 * mm

    # ==========================
    # QR CODE (Bottom Center)
    # ==========================
    y -= 10 * mm

    qr = _generate_invoice_qr_image(invoice, request)
    qr_size = 25 * mm
    qr_x = (w - qr_size) / 2
    pdf.drawImage(qr, qr_x, y - qr_size, width=qr_size, height=qr_size)

    y -= qr_size + 4 * mm

    pdf.setFont("Helvetica", 6)
    pdf.setFillColor(GRAY)
    pdf.drawCentredString(w / 2, y, "Scan To Verify Invoice")
    pdf.setFillColor(DARK)

    # ==========================
    # FOOTER
    # ==========================
    y -= 6 * mm
    pdf.setFont("Helvetica-Bold", 7)
    pdf.setFillColor(DARK)
    pdf.drawCentredString(w / 2, y, "Thank You For Dining With Us")

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.invoice_number}.pdf"'
    return response

# =========================
# INVOICE VERIFY (via QR)
# =========================
def invoice_verify(request, uuid_token):
    invoice = Invoice.objects.filter(uuid_token=uuid_token).first()

    if not invoice:
        return render(request, "food-delivery/invoice_verify.html", {
            "valid": False,
            "error": "Invoice not found. The link may be invalid or the invoice has been removed.",
        })

    order = getattr(invoice, 'kitchen_order', None)
    items = invoice.items.all()
    subtotal = sum(float(item.subtotal) for item in items)
    tax_pct = float(invoice.tax_percentage) if invoice.tax_percentage else 5
    tax = float(invoice.tax_amount) if invoice.tax_amount else round(subtotal * tax_pct / 100, 2)

    customer_name = invoice.customer_name or (invoice.user.name if invoice.user else "Walk-in Customer")
    customer_email = invoice.customer_email or (invoice.user.email if invoice.user else "N/A")

    invoice_date = timezone.localtime(invoice.created_at).strftime("%d-%m-%Y %I:%M:%S %p")

    context = {
        "valid": True,
        "invoice": invoice,
        "order": order,
        "items": items,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "subtotal": subtotal,
        "tax": tax,
        "tax_pct": tax_pct,
        "payment_method": invoice.payment_method or "N/A",
        "status": order.status if order else "pending",
        "status_display": order.get_status_display() if order else "Pending",
        "order_no": order.order_number if order else "N/A",
        "invoice_date": invoice_date,
    }
    return render(request, "food-delivery/invoice_verify.html", context)


# =========================
# ADMIN DASHBOARD
# =========================
@staff_member_required
def admin_dashboard(request):
    foods_count = Food.objects.count()
    invoices_count = Invoice.objects.count()
    users_count = User.objects.count()
    tables_count = RestaurantTable.objects.count()
    kitchen_users_count = User.objects.filter(is_kitchen=True).count()
    customers_count = User.objects.filter(is_staff=False, is_kitchen=False, is_superuser=False).count()

    # Loyalty stats
    from django.db.models import Sum
    loyalty_cards_count = LoyaltyCard.objects.count()
    loyalty_active = LoyaltyCard.objects.filter(status='ACTIVE').count()
    loyalty_points_earned = LoyaltyCard.objects.aggregate(total=Sum('total_points'))['total'] or 0
    loyalty_points_redeemed = LoyaltyCard.objects.aggregate(total=Sum('used_points'))['total'] or 0

    # Offer & Deal stats
    total_offers = TimeBasedOffer.objects.count()
    active_offers = TimeBasedOffer.objects.filter(is_active=True).count()
    expired_offers = TimeBasedOffer.objects.filter(is_active=False).count()
    total_deals = TodayDeal.objects.count()
    active_deals = TodayDeal.objects.filter(is_active=True).count()
    offer_usage = Invoice.objects.aggregate(total=Sum('qr_offer_discount_amount'))['total'] or 0
    offer_discount_given = Invoice.objects.filter(qr_offer_discount_amount__gt=0).count()

    pending_count = KitchenOrder.objects.filter(status="pending").count()
    preparing_count = KitchenOrder.objects.filter(status="preparing").count()
    ready_count = KitchenOrder.objects.filter(status="ready").count()
    delivered_count = KitchenOrder.objects.filter(status="delivered").count()
    active_orders = KitchenOrder.objects.exclude(status="delivered").count()

    revenue = Invoice.objects.aggregate(total=Sum("total_amount"))["total"] or 0

    card_tax = Invoice.objects.filter(payment_method__iexact="card").aggregate(total=Sum("tax_amount"))["total"] or 0
    cash_tax = Invoice.objects.filter(payment_method__iexact="cash").aggregate(total=Sum("tax_amount"))["total"] or 0
    if float(card_tax) == 0 and float(cash_tax) == 0:
        total_card_subtotal = Invoice.objects.filter(payment_method__iexact="card").aggregate(total=Sum("subtotal_amount"))["total"] or 0
        total_cash_subtotal = Invoice.objects.filter(payment_method__iexact="cash").aggregate(total=Sum("subtotal_amount"))["total"] or 0
        card_tax = round(float(total_card_subtotal) * 0.05, 2)
        cash_tax = round(float(total_cash_subtotal) * 0.18, 2)
    total_tax = round(float(card_tax) + float(cash_tax), 2)

    # Recent orders
    recent_orders = KitchenOrder.objects.select_related("invoice").order_by("-created_at")[:20]

    # Table reports
    tables = RestaurantTable.objects.all()
    table_reports = []
    for table in tables:
        ti = Invoice.objects.filter(table_no=table.table_no)
        table_reports.append({
            "table": table,
            "orders_count": ti.count(),
            "revenue": float(ti.aggregate(total=Sum("total_amount"))["total"] or 0),
        })

    return render(request, "admin/dashboard.html", {
        "foods_count": foods_count,
        "invoices_count": invoices_count,
        "users_count": users_count,
        "tables_count": tables_count,
        "kitchen_users_count": kitchen_users_count,
        "customers_count": customers_count,
        "revenue": revenue,
        "total_tax": total_tax,
        "card_tax": card_tax,
        "cash_tax": cash_tax,
        "pending_count": pending_count,
        "preparing_count": preparing_count,
        "ready_count": ready_count,
        "delivered_count": delivered_count,
        "active_orders": active_orders,
        "total_orders": invoices_count,
        "recent_orders": recent_orders,
        "table_reports": table_reports,
        "loyalty_cards_count": loyalty_cards_count,
        "loyalty_active": loyalty_active,
        "loyalty_points_earned": loyalty_points_earned,
        "loyalty_points_redeemed": loyalty_points_redeemed,
        "total_offers": total_offers,
        "active_offers": active_offers,
        "expired_offers": expired_offers,
        "total_deals": total_deals,
        "active_deals": active_deals,
        "offer_usage": offer_usage,
        "offer_discount_given": offer_discount_given,
    })


@staff_member_required
def revenue_filter(request):
    try:
        start_str = request.GET.get("start_date")
        end_str = request.GET.get("end_date")
        invoices = Invoice.objects.all()
        if start_str and end_str:
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                end_dt = datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)
                start_utc = timezone.make_aware(start_dt, dt_timezone.utc)
                end_utc = timezone.make_aware(end_dt, dt_timezone.utc)
                invoices = invoices.filter(created_at__range=[start_utc, end_utc])
            except (ValueError, TypeError):
                return JsonResponse({"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}, status=400)
        revenue = invoices.aggregate(total=Sum("total_amount"))["total"] or 0
        return JsonResponse({"success": True, "revenue": float(revenue)})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@staff_member_required
def tax_analytics(request):
    try:
        start_str = request.GET.get("start_date")
        end_str = request.GET.get("end_date")
        invoices = Invoice.objects.all()
        if start_str and end_str:
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                end_dt = datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)
                start_utc = timezone.make_aware(start_dt, dt_timezone.utc)
                end_utc = timezone.make_aware(end_dt, dt_timezone.utc)
                invoices = invoices.filter(created_at__range=[start_utc, end_utc])
            except (ValueError, TypeError):
                return JsonResponse({"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        revenue = invoices.aggregate(total=Sum("total_amount"))["total"] or 0

        card_tax = invoices.filter(payment_method__iexact="card").aggregate(total=Sum("tax_amount"))["total"] or 0
        cash_tax = invoices.filter(payment_method__iexact="cash").aggregate(total=Sum("tax_amount"))["total"] or 0

        if float(card_tax) == 0 and float(cash_tax) == 0:
            total_card_subtotal = invoices.filter(payment_method__iexact="card").aggregate(total=Sum("subtotal_amount"))["total"] or 0
            total_cash_subtotal = invoices.filter(payment_method__iexact="cash").aggregate(total=Sum("subtotal_amount"))["total"] or 0
            card_tax = round(float(total_card_subtotal) * 0.05, 2)
            cash_tax = round(float(total_cash_subtotal) * 0.18, 2)

        total_tax = round(float(card_tax) + float(cash_tax), 2)

        return JsonResponse({
            "success": True,
            "revenue": float(revenue),
            "total_tax": total_tax,
            "card_tax": float(card_tax),
            "cash_tax": float(cash_tax),
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# =========================
# PRODUCT MANAGEMENT
# =========================
@staff_member_required
def product_list(request):
    products = Food.objects.all()
    return render(request, "admin/products.html", {"products": products})


@staff_member_required
def add_product(request):
    categories = Category.objects.all()
    if request.method == "POST":
        category = Category.objects.get(id=request.POST.get("category"))
        Food.objects.create(
            category=category, name=request.POST.get("name"),
            description=request.POST.get("description"),
            price=request.POST.get("price"),
            reward_points=request.POST.get("reward_points", 0),
            image=request.FILES.get("image"),
            available=request.POST.get("available") == "on",
        )
        messages.success(request, "Product added successfully.")
        return redirect("users:product_list")
    return render(request, "admin/add_product.html", {"categories": categories})


@staff_member_required
def edit_product(request, pk):
    product = get_object_or_404(Food, pk=pk)
    categories = Category.objects.all()
    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.reward_points = request.POST.get("reward_points", 0)
        product.category = get_object_or_404(Category, id=request.POST.get("category_id"))
        product.available = request.POST.get("available") == "on"
        if request.FILES.get("image"):
            product.image = request.FILES.get("image")
        product.save()
        messages.success(request, "Product updated successfully")
        return redirect("users:product_list")
    return render(request, "admin/edit_product.html", {"product": product, "categories": categories})


@staff_member_required
def delete_product(request, pk):
    product = get_object_or_404(Food, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully")
    return redirect("users:product_list")


# =========================
# SEARCH / DATA
# =========================
@csrf_exempt
def search_invoice(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email", "")
        search = data.get("search", "")
        q = search or email
        invoices = Invoice.objects.filter(
            Q(user__email__icontains=q) |
            Q(customer_email__icontains=q) |
            Q(invoice_number__icontains=q)
        )[:20]
        return JsonResponse({
            "invoices": [{
                "id": inv.id,
                "uuid_token": inv.uuid_token,
                "invoice_number": inv.invoice_number,
                "name": inv.customer_name or (inv.user.name if inv.user else ""),
                "email": inv.customer_email or (inv.user.email if inv.user else ""),
                "total": float(inv.total_amount),
                "status": getattr(getattr(inv, 'kitchen_order', None), 'status', 'pending'),
            } for inv in invoices]
        })
    return JsonResponse({"invoices": []})


@staff_member_required
def search_users(request):
    users = User.objects.all()
    return JsonResponse({
        "users": [{"id": u.id, "email": u.email, "name": u.name} for u in users]
    })


# =========================
# KITCHEN DASHBOARD
# =========================
@login_required
def kitchen_dashboard(request):
    if not request.user.is_kitchen:
        return JsonResponse({"message": "Access denied"}, status=403)

    orders = KitchenOrder.objects.select_related("invoice").order_by("-created_at")
    latest_order_id = orders.first().id if orders.exists() else 0

    pending_orders = orders.filter(status="pending")
    preparing_orders = orders.filter(status="preparing")
    ready_orders = orders.filter(status="ready")
    delivered_orders = orders.filter(status="delivered")

    return render(request, "kitchen/dashboard.html", {
        "orders": orders,
        "pending_orders": pending_orders,
        "preparing_orders": preparing_orders,
        "ready_orders": ready_orders,
        "delivered_orders": delivered_orders,
        "latest_order_id": latest_order_id,
    })


@login_required
def update_order_status(request, order_id):
    if not request.user.is_kitchen:
        return redirect("users:kitchen_dashboard")

    order = KitchenOrder.objects.get(id=order_id)
    new_status = request.POST.get("status")
    order.status = new_status
    order.save()

    if new_status == "delivered":
        try:
            invoice = order.invoice
            invoice.generate_qr_code(request)
            invoice.save()

            # Auto-earn loyalty points for delivered orders (online users only)
            if invoice.user and not invoice.loyalty_points_processed:
                card = LoyaltyCard.objects.filter(user=invoice.user, status='ACTIVE').first()
                if card:
                    total_points = 0
                    for inv_item in invoice.items.all():
                        from menu.models import Food
                        food = Food.objects.filter(
                            Q(name__iexact=inv_item.product_name.strip()) |
                            Q(name__icontains=inv_item.product_name.strip())
                        ).first()
                        if food and food.reward_points > 0:
                            total_points += food.reward_points * inv_item.quantity
                    if total_points > 0:
                        card.add_points(total_points, order.order_number)
                        invoice.loyalty_points_earned = total_points
                        invoice.loyalty_points_processed = True
                        invoice.save()
        except Exception:
            pass

    return redirect("users:kitchen_dashboard")


def kitchen_search_orders(request):
    q = request.GET.get("q", "")
    orders = KitchenOrder.objects.select_related("invoice").order_by("-created_at")
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(invoice__invoice_number__icontains=q) |
            Q(table_no__icontains=q) |
            Q(status__icontains=q)
        )
    latest = KitchenOrder.objects.order_by("-id").first()
    return JsonResponse({
        "latest_order_id": latest.id if latest else 0,
        "orders": [{
            "id": o.id, "order_number": o.order_number,
            "invoice_no": o.invoice.invoice_number,
            "table_no": o.table_no, "status": o.status,
            "created_at": timezone.localtime(o.created_at).strftime("%d-%m-%Y %I:%M:%S %p"),
            "items": list(o.items.values("product_name", "quantity")),
            "total_amount": float(o.invoice.total_amount),
        } for o in orders]
    })


# =========================
# KITCHEN USER MANAGEMENT
# =========================
@staff_member_required
@csrf_exempt
def create_kitchen(request):
    if request.method == "POST":
        data = json.loads(request.body)
        if User.objects.filter(email=data.get("email")).exists():
            return JsonResponse({"message": "Email already exists"}, status=400)
        user = User.objects.create_user(name=data.get("name"), email=data.get("email"), password=data.get("password"))
        user.is_kitchen = True
        user.is_staff = False
        user.is_superuser = False
        user.save()
        return JsonResponse({"message": "Kitchen user created"})
    return JsonResponse({"message": "Invalid request"}, status=400)


@staff_member_required
def kitchen_list(request):
    kitchens = User.objects.filter(is_kitchen=True)
    return JsonResponse({
        "kitchens": [{"id": k.id, "name": k.name, "email": k.email} for k in kitchens]
    })


@csrf_exempt
def edit_kitchen(request, id):
    if request.method != "POST":
        return JsonResponse({"message": "Invalid request"}, status=400)
    try:
        user = User.objects.get(id=id, is_kitchen=True)
        data = json.loads(request.body)
        user.name = data.get("name")
        user.save()
        return JsonResponse({"message": "Kitchen user updated"})
    except User.DoesNotExist:
        return JsonResponse({"message": "Kitchen user not found"}, status=404)


@csrf_exempt
def delete_kitchen(request, id):
    User.objects.get(id=id).delete()
    return JsonResponse({"message": "Kitchen user deleted"})


# =========================
# ORDER SEARCH / FILTERS
# =========================
def search_order(request):
    order_no = request.GET.get("order_no")
    try:
        order = KitchenOrder.objects.get(order_number__iexact=order_no)
        return JsonResponse({
            "found": True, "order_number": order.order_number,
            "status": order.status, "table_no": order.table_no,
            "created_at": timezone.localtime(order.created_at).strftime("%d-%m-%Y %I:%M %p"),
            "invoice_no": order.invoice.invoice_number,
            "total_amount": float(order.invoice.total_amount),
            "items": list(order.items.values("product_name", "quantity")),
        })
    except KitchenOrder.DoesNotExist:
        return JsonResponse({"found": False})


@staff_member_required
def orders_by_date(request):
    date = request.GET.get("date")
    order_dir = request.GET.get("order", "desc")
    orders = KitchenOrder.objects.all()
    if date:
        orders = orders.filter(created_at__date=date)

    pending_count = orders.filter(status="pending").count()
    preparing_count = orders.filter(status="preparing").count()
    ready_count = orders.filter(status="ready").count()
    delivered_count = orders.filter(status="delivered").count()

    if order_dir == "asc":
        orders = orders.order_by("created_at")
    else:
        orders = orders.order_by("-created_at")

    return JsonResponse({
        "pending_count": pending_count, "preparing_count": preparing_count,
        "ready_count": ready_count, "delivered_count": delivered_count,
        "orders": [{
            "id": o.id, "order_number": o.order_number, "status": o.status,
            "table_no": o.table_no,
            "created_at": timezone.localtime(o.created_at).strftime("%d-%m-%Y %I:%M %p"),
            "uuid_token": o.invoice.uuid_token,
            "invoice_no": o.invoice.invoice_number,
            "total_amount": float(o.invoice.total_amount),
        } for o in orders]
    })


@staff_member_required
def orders_by_status(request):
    status = request.GET.get("status")
    orders = KitchenOrder.objects.filter(status=status).order_by("-created_at")
    return JsonResponse({
        "orders": [{
            "id": o.id, "order_number": o.order_number, "status": o.status,
            "table_no": o.table_no,
            "created_at": timezone.localtime(o.created_at).strftime("%d-%m-%Y %I:%M %p"),
            "uuid_token": o.invoice.uuid_token,
            "invoice_no": o.invoice.invoice_number,
            "total_amount": float(o.invoice.total_amount),
        } for o in orders],
        "count": orders.count()
    })


# =========================
# MY ORDERS
# =========================
def my_orders(request):
    if request.user.is_authenticated:
        invoices = Invoice.objects.filter(user=request.user).select_related("kitchen_order").order_by("-id")[:10]
    else:
        session_id = request.session.get("customer_session_id")
        if session_id:
            invoices = Invoice.objects.filter(customer_session_id=session_id).select_related("kitchen_order").order_by("-id")[:10]
        else:
            invoices = Invoice.objects.none()
    return JsonResponse({
        "orders": [{
            "invoice": i.invoice_number, "uuid_token": i.uuid_token,
            "order_no": i.kitchen_order.order_number if i.kitchen_order else "",
            "status": i.kitchen_order.status if i.kitchen_order else "pending",
            "table_no": i.table_no,
            "created_at": timezone.localtime(i.created_at).strftime("%d-%m-%Y %I:%M %p"),
        } for i in invoices]
    })


# =========================
# INVOICE SEARCH PAGE
# =========================
@staff_member_required
def invoice_search_page(request):
    return render(request, "admin/invoices.html")


# =========================
# KITCHEN USERS PAGE
# =========================
@staff_member_required
def kitchen_users_page(request):
    return render(request, "admin/kitchen_users.html")


# =========================
# TABLE MANAGEMENT
# =========================
@staff_member_required
def table_list(request):
    tables = RestaurantTable.objects.all().order_by("table_no")
    return render(request, "admin/tables.html", {"tables": tables})


@staff_member_required
def add_table(request):
    if request.method == "POST":
        table_no = request.POST.get("table_no")
        if not table_no:
            messages.error(request, "Table number is required.")
            return redirect("users:table_list")
        if RestaurantTable.objects.filter(table_no=table_no).exists():
            messages.error(request, f"Table {table_no} already exists.")
            return redirect("users:table_list")
        table = RestaurantTable.objects.create(table_no=table_no)
        table.generate_qr_code(request)
        table.save()
        messages.success(request, f"Table {table_no} added successfully.")
    return redirect("users:table_list")


@staff_member_required
def edit_table(request, pk):
    if request.method == "POST":
        table = get_object_or_404(RestaurantTable, pk=pk)
        new_no = request.POST.get("table_no")
        if new_no and str(new_no) != str(table.table_no):
            if RestaurantTable.objects.filter(table_no=new_no).exists():
                messages.error(request, f"Table {new_no} already exists.")
                return redirect("users:table_list")
            table.table_no = new_no
        if request.POST.get("regenerate_qr"):
            table.generate_qr_code(request)
        table.save()
        messages.success(request, "Table updated.")
    return redirect("users:table_list")


@staff_member_required
def delete_table(request, pk):
    table = get_object_or_404(RestaurantTable, pk=pk)
    table.delete()
    messages.success(request, f"Table deleted.")
    return redirect("users:table_list")


@staff_member_required
def generate_table_qr(request, pk):
    table = get_object_or_404(RestaurantTable, pk=pk)
    table.generate_qr_code(request)
    table.save()
    messages.success(request, f"QR generated for Table {table.table_no}.")
    return redirect("users:table_list")


# =========================
# MYSQL BACKUP
# =========================


@staff_member_required
def mysql_backup(request):
    db = settings.DATABASES["default"]
    MYSQLDUMP_PATH = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
    result = subprocess.run(
        [MYSQLDUMP_PATH, f"--user={db['USER']}", f"--password={db['PASSWORD']}", db["NAME"]],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return HttpResponse(result.stderr, status=500)
    response = HttpResponse(result.stdout, content_type="application/sql")
    response["Content-Disposition"] = 'attachment; filename="database_backup.sql"'
    return response


# =============================================================================
# LOYALTY CARD VIEWS
# =============================================================================

@login_required
def loyalty_card_view(request):
    if request.user.is_staff or request.user.is_superuser or getattr(request.user, 'is_kitchen', False):
        messages.error(request, "Loyalty cards are only available for customers.")
        return redirect('/')
    card = LoyaltyCard.objects.filter(user=request.user).first()
    if not card:
        card = LoyaltyCard.objects.create(user=request.user, status='ACTIVE')
    qr_ok = card.qr_code_image and card.qr_code_image.storage.exists(card.qr_code_image.name)
    if not qr_ok:
        try:
            generate_qr_code_image(card, request)
        except Exception:
            pass
    if not card.card_pdf or not card.card_image:
        try:
            generate_loyalty_card_pdf(card, request)
            generate_loyalty_card_image(card, request)
        except Exception:
            pass
    show_welcome = not card.first_card_popup_shown
    if show_welcome:
        card.first_card_popup_shown = True
        card.save(update_fields=['first_card_popup_shown'])
    transactions = LoyaltyTransaction.objects.filter(card=card).order_by('-created_at')
    return render(request, 'users/loyalty_card.html', {
        'card': card,
        'transactions': transactions,
        'show_welcome': show_welcome,
    })


@login_required
def download_loyalty_pdf(request, card_number):
    try:
        card = get_object_or_404(LoyaltyCard, card_number=card_number, user=request.user)
        if not card.qr_code_image or not card.qr_code_image.storage.exists(card.qr_code_image.name):
            generate_qr_code_image(card, request)
            card.refresh_from_db()
        if not card.card_pdf or not card.card_pdf.storage.exists(card.card_pdf.name):
            card = generate_loyalty_card_pdf(card, request)
        card.card_pdf.open('rb')
        response = FileResponse(card.card_pdf, as_attachment=True, filename=f"loyalty_card_{card.card_number}.pdf")
        response['Content-Type'] = 'application/pdf'
        response['Content-Disposition'] = f'attachment; filename="loyalty_card_{card.card_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Could not generate PDF. Please try again. Error: {str(e)}")
        return redirect('users:loyalty_card_view')


@login_required
def download_loyalty_image(request, card_number):
    try:
        card = get_object_or_404(LoyaltyCard, card_number=card_number, user=request.user)
        if not card.qr_code_image or not card.qr_code_image.storage.exists(card.qr_code_image.name):
            generate_qr_code_image(card, request)
            card.refresh_from_db()
        if not card.card_image or not card.card_image.storage.exists(card.card_image.name):
            card = generate_loyalty_card_image(card, request)
        card.card_image.open('rb')
        response = FileResponse(card.card_image, as_attachment=True, filename=f"loyalty_card_{card.card_number}.png")
        response['Content-Type'] = 'image/png'
        response['Content-Disposition'] = f'attachment; filename="loyalty_card_{card.card_number}.png"'
        return response
    except Exception as e:
        messages.error(request, f"Could not generate card image. Please try again. Error: {str(e)}")
        return redirect('users:loyalty_card_view')


@login_required
def loyalty_card_data(request):
    card = LoyaltyCard.objects.filter(user=request.user).first()
    if not card:
        return JsonResponse({'has_card': False})
    return JsonResponse({
        'has_card': True,
        'card_number': card.card_number,
        'total_points': card.total_points,
        'used_points': card.used_points,
        'remaining_points': card.remaining_points,
        'status': card.status,
    })


@login_required
def loyalty_checkout_info(request):
    card = LoyaltyCard.objects.filter(user=request.user, status='ACTIVE').first()
    if card:
        return JsonResponse({
            'has_card': True,
            'total_points': card.total_points,
            'remaining_points': card.remaining_points,
            'card_number': card.card_number,
        })
    return JsonResponse({'has_card': False})


@csrf_exempt
def verify_loyalty_qr(request, qr_token):
    if request.method == 'GET':
        card = LoyaltyCard.objects.filter(qr_token=qr_token).first()
        if not card:
            return JsonResponse({'valid': False, 'error': 'Invalid Loyalty Card'}, status=404)
        if card.status != 'ACTIVE':
            return JsonResponse({'valid': False, 'error': 'Loyalty Card is blocked'}, status=403)
        user_name = card.user.name if card.user else 'Customer'
        return JsonResponse({
            'valid': True,
            'card_number': card.card_number,
            'customer': user_name,
            'card_status': card.status,
        })
    return JsonResponse({'valid': False}, status=405)


def qr_loyalty_redirect(request, qr_token):
    card = LoyaltyCard.objects.filter(qr_token=qr_token).first()
    if not card:
        messages.error(request, "Invalid Loyalty Card")
        return redirect("users:login")
    if card.status != 'ACTIVE':
        messages.error(request, "Loyalty Card is blocked")
        return redirect("users:login")
    if not request.user.is_authenticated:
        login_url = reverse("users:login")
        next_url = reverse("users:qr_loyalty_redirect", args=[qr_token])
        return redirect(f"{login_url}?next={next_url}")
    if card.user != request.user:
        messages.error(request, "Invalid Loyalty Card")
        return redirect("users:login")
    return redirect("users:loyalty_card_view")


@csrf_exempt
@login_required
def loyalty_checkout_validate(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            total_amount = float(data.get('total_amount', 0))
            use_points = data.get('use_points')
            if use_points is not None:
                use_points = int(use_points)
            card = LoyaltyCard.objects.filter(user=request.user, status='ACTIVE').first()
            if not card:
                return JsonResponse({'can_pay': False, 'error': 'No active loyalty card found'})
            available = card.remaining_points
            if available <= 0:
                return JsonResponse({
                    'can_pay': False,
                    'error': 'No loyalty points available.',
                    'available_points': 0,
                })
            max_allowed = min(available, int(total_amount))
            if use_points is None:
                use_points = max_allowed
            elif use_points < 0:
                return JsonResponse({'can_pay': False, 'error': 'Points cannot be negative', 'available_points': available})
            elif use_points > available:
                return JsonResponse({
                    'can_pay': False,
                    'error': f'You only have {available} loyalty points available.',
                    'available_points': available,
                })
            elif use_points > int(total_amount):
                use_points = int(total_amount)
            remaining_due = int(total_amount) - use_points
            return JsonResponse({
                'can_pay': True,
                'available_points': available,
                'points_to_use': use_points,
                'remaining_due': remaining_due if remaining_due > 0 else 0,
                'needs_secondary': remaining_due > 0,
                'card_number': card.card_number,
            })
        except Exception as e:
            return JsonResponse({'can_pay': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)


# Admin loyalty views
@staff_member_required
def admin_loyalty_list(request):
    cards = LoyaltyCard.objects.select_related('user').all().order_by('-created_at')
    search = request.GET.get('search', '')
    if search:
        cards = cards.filter(
            Q(card_number__icontains=search) |
            Q(user__name__icontains=search) |
            Q(user__email__icontains=search)
        )
    status_filter = request.GET.get('status', '')
    if status_filter:
        cards = cards.filter(status=status_filter)
    return render(request, 'users/admin_loyalty_list.html', {
        'cards': cards,
        'search': search,
        'status_filter': status_filter,
    })


@staff_member_required
def admin_loyalty_detail(request, card_number):
    card = get_object_or_404(LoyaltyCard, card_number=card_number)
    transactions = LoyaltyTransaction.objects.filter(card=card).order_by('-created_at')
    return render(request, 'users/admin_loyalty_detail.html', {
        'card': card,
        'transactions': transactions,
    })


@staff_member_required
def admin_toggle_card_status(request, card_number):
    card = get_object_or_404(LoyaltyCard, card_number=card_number)
    if request.method == 'POST':
        card.status = 'BLOCKED' if card.status == 'ACTIVE' else 'ACTIVE'
        card.save()
        messages.success(request, f"Card {card.card_number} is now {card.get_status_display()}")
    return redirect('users:admin_loyalty_detail', card_number=card.card_number)


@staff_member_required
def admin_reset_points(request, card_number):
    card = get_object_or_404(LoyaltyCard, card_number=card_number)
    if request.method == 'POST':
        card.total_points = 0
        card.used_points = 0
        card.remaining_points = 0
        card.save()
        LoyaltyTransaction.objects.filter(card=card).delete()
        messages.success(request, f"Points reset for card {card.card_number}")
    return redirect('users:admin_loyalty_detail', card_number=card.card_number)


@staff_member_required
def admin_loyalty_reports(request):
    total_cards = LoyaltyCard.objects.count()
    active_cards = LoyaltyCard.objects.filter(status='ACTIVE').count()
    blocked_cards = LoyaltyCard.objects.filter(status='BLOCKED').count()
    total_earned = LoyaltyCard.objects.aggregate(total=models.Sum('total_points'))['total'] or 0
    total_redeemed = LoyaltyCard.objects.aggregate(total=models.Sum('used_points'))['total'] or 0
    total_remaining = LoyaltyCard.objects.aggregate(total=models.Sum('remaining_points'))['total'] or 0

    loyalty_revenue = Invoice.objects.filter(is_loyalty_payment=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    context = {
        'total_cards': total_cards,
        'active_cards': active_cards,
        'blocked_cards': blocked_cards,
        'total_earned': total_earned,
        'total_redeemed': total_redeemed,
        'total_remaining': total_remaining,
        'loyalty_revenue': loyalty_revenue,
    }
    return render(request, 'users/admin_loyalty_reports.html', context)


@staff_member_required
def admin_export_loyalty_csv(request):
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loyalty_cards_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Card Number', 'Customer', 'Email', 'Total Points', 'Used Points', 'Remaining', 'Status', 'Created'])
    for card in LoyaltyCard.objects.select_related('user').all():
        writer.writerow([
            card.card_number,
            card.user.name if card.user else 'N/A',
            card.user.email if card.user else 'N/A',
            card.total_points,
            card.used_points,
            card.remaining_points,
            card.status,
            card.created_at.strftime('%d-%m-%Y'),
        ])
    return response


@login_required
def loyalty_transactions(request):
    card = LoyaltyCard.objects.filter(user=request.user).first()
    if not card:
        return JsonResponse({'transactions': []})
    transactions = LoyaltyTransaction.objects.filter(card=card).order_by('-created_at')
    return JsonResponse({
        'transactions': [{
            'id': t.id,
            'order_number': t.order_number,
            'earned_points': t.earned_points,
            'redeemed_points': t.redeemed_points,
            'remaining_balance': t.remaining_balance,
            'transaction_type': t.transaction_type,
            'created_at': t.created_at.strftime('%d-%m-%Y %I:%M %p'),
        } for t in transactions],
    })


# =========================
# OFFERS & DEALS API
# =========================
def active_offer_data(request):
    offer = TimeBasedOffer.objects.filter(is_active=True).first()
    if not offer:
        return JsonResponse({"active": False})
    now = timezone.now()
    end_dt = timezone.make_aware(
        datetime.combine(offer.end_date, offer.end_time)
    )
    return JsonResponse({
        "active": True,
        "id": offer.id,
        "title": offer.title,
        "description": offer.description or "",
        "discount_percentage": float(offer.discount_percentage),
        "banner_image": offer.banner_image.url if offer.banner_image else "",
        "background_color": offer.background_color or "#f59e0b",
        "popup_image": offer.popup_image.url if offer.popup_image else "",
        "start_date": offer.start_date.strftime("%d-%m-%Y"),
        "start_time": offer.start_time.strftime("%I:%M %p"),
        "end_date": offer.end_date.strftime("%d-%m-%Y"),
        "end_time": offer.end_time.strftime("%I:%M %p"),
        "end_timestamp": int(end_dt.timestamp()),
    })


def active_deal_data(request):
    deal = TodayDeal.objects.filter(is_active=True).first()
    if not deal:
        return JsonResponse({"active": False})
    now = timezone.now()
    end_dt = timezone.make_aware(
        datetime.combine(deal.end_date, deal.end_time)
    )
    deal_products = deal.products.all()
    products_data = []
    original_total = 0
    for p in deal_products:
        products_data.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "image": p.image.url if p.image else "",
        })
        original_total += float(p.price)
    if deal.free_product:
        products_data.append({
            "id": deal.free_product.id,
            "name": deal.free_product.name + " (Free)",
            "price": float(deal.free_product.price),
            "image": deal.free_product.image.url if deal.free_product.image else "",
            "free": True,
        })
        original_total += float(deal.free_product.price)
    savings = 0
    if deal.combo_price and original_total > 0:
        savings = original_total - float(deal.combo_price)
        if savings < 0:
            savings = 0
    return JsonResponse({
        "active": True,
        "id": deal.id,
        "title": deal.title,
        "description": deal.description or "",
        "deal_image": deal.deal_image.url if deal.deal_image else "",
        "deal_banner": deal.deal_banner.url if deal.deal_banner else "",
        "products": products_data,
        "combo_price": float(deal.combo_price) if deal.combo_price else None,
        "original_total": original_total,
        "savings": savings,
        "start_date": deal.start_date.strftime("%d-%m-%Y"),
        "start_time": deal.start_time.strftime("%I:%M %p"),
        "end_date": deal.end_date.strftime("%d-%m-%Y"),
        "end_time": deal.end_time.strftime("%I:%M %p"),
        "end_timestamp": int(end_dt.timestamp()),
    })


def offer_banner_data(request):
    offer = TimeBasedOffer.objects.filter(is_active=True).first()
    deal = TodayDeal.objects.filter(is_active=True).first()
    data = {"offer": None, "deal": None}
    if offer:
        end_dt = timezone.make_aware(
            datetime.combine(offer.end_date, offer.end_time)
        )
        data["offer"] = {
            "title": offer.title,
            "discount_percentage": float(offer.discount_percentage),
            "background_color": offer.background_color or "#f59e0b",
            "end_timestamp": int(end_dt.timestamp()),
        }
    if deal:
        end_dt = timezone.make_aware(
            datetime.combine(deal.end_date, deal.end_time)
        )
        deal_products = deal.products.all()
        original_total = sum(float(p.price) for p in deal_products)
        if deal.free_product:
            original_total += float(deal.free_product.price)
        savings = 0
        if deal.combo_price and original_total > 0:
            savings = original_total - float(deal.combo_price)
            if savings < 0:
                savings = 0
        data["deal"] = {
            "id": deal.id,
            "title": deal.title,
            "description": deal.description or "",
            "deal_banner": deal.deal_banner.url if deal.deal_banner else "",
            "combo_price": float(deal.combo_price) if deal.combo_price else None,
            "original_total": original_total,
            "savings": savings,
            "end_timestamp": int(end_dt.timestamp()),
        }
    return JsonResponse(data)


# =========================
# OFFER CRUD VIEWS
# =========================
@staff_member_required
def offer_list(request):
    offers = TimeBasedOffer.objects.all().order_by("-created_at")
    total_offers = offers.count()
    active_offers = offers.filter(is_active=True).count()
    expired_offers = total_offers - active_offers
    usage_count = Invoice.objects.filter(qr_offer_discount_amount__gt=0).count()
    return render(request, "admin/offer_list.html", {
        "offers": offers,
        "total_offers": total_offers,
        "active_offers": active_offers,
        "expired_offers": expired_offers,
        "usage_count": usage_count,
        "active_page": "offers",
    })


@staff_member_required
def offer_add(request):
    if request.method == "POST":
        try:
            offer = TimeBasedOffer(
                title=request.POST.get("title"),
                description=request.POST.get("description", ""),
                discount_percentage=request.POST.get("discount_percentage", 0),
                background_color=request.POST.get("background_color", "#f59e0b"),
                is_active=request.POST.get("is_active") == "1",
                start_date=request.POST.get("start_date"),
                start_time=request.POST.get("start_time"),
                end_date=request.POST.get("end_date"),
                end_time=request.POST.get("end_time"),
            )
            if "banner_image" in request.FILES:
                offer.banner_image = request.FILES["banner_image"]
            if "popup_image" in request.FILES:
                offer.popup_image = request.FILES["popup_image"]
            offer.save()
            messages.success(request, "Offer created successfully.")
            return redirect("users:offer_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "admin/offer_form.html", {"active_page": "offers"})


@staff_member_required
def offer_edit(request, pk):
    offer = get_object_or_404(TimeBasedOffer, pk=pk)
    if request.method == "POST":
        try:
            offer.title = request.POST.get("title")
            offer.description = request.POST.get("description", "")
            offer.discount_percentage = request.POST.get("discount_percentage", 0)
            offer.background_color = request.POST.get("background_color", "#f59e0b")
            offer.is_active = request.POST.get("is_active") == "1"
            offer.start_date = request.POST.get("start_date")
            offer.start_time = request.POST.get("start_time")
            offer.end_date = request.POST.get("end_date")
            offer.end_time = request.POST.get("end_time")
            if "banner_image" in request.FILES:
                offer.banner_image = request.FILES["banner_image"]
            if "popup_image" in request.FILES:
                offer.popup_image = request.FILES["popup_image"]
            offer.save()
            messages.success(request, "Offer updated successfully.")
            return redirect("users:offer_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "admin/offer_form.html", {"offer": offer, "active_page": "offers"})


@staff_member_required
def offer_detail(request, pk):
    offer = get_object_or_404(TimeBasedOffer, pk=pk)
    return render(request, "admin/offer_detail.html", {"offer": offer, "active_page": "offers"})


@staff_member_required
def offer_delete(request, pk):
    offer = get_object_or_404(TimeBasedOffer, pk=pk)
    if request.method == "POST":
        try:
            offer.delete()
            messages.success(request, "Offer deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return redirect("users:offer_list")


# =========================
# DEAL CRUD VIEWS
# =========================
@staff_member_required
def deal_list(request):
    deals = TodayDeal.objects.all().order_by("-created_at")
    total_deals = deals.count()
    active_deals = deals.filter(is_active=True).count()
    expired_deals = total_deals - active_deals
    return render(request, "admin/deal_list.html", {
        "deals": deals,
        "total_deals": total_deals,
        "active_deals": active_deals,
        "expired_deals": expired_deals,
        "active_page": "deals",
    })


@staff_member_required
def deal_add(request):
    products = Food.objects.all()
    if request.method == "POST":
        try:
            deal = TodayDeal(
                title=request.POST.get("title"),
                description=request.POST.get("description", ""),
                is_active=request.POST.get("is_active") == "1",
                start_date=request.POST.get("start_date"),
                start_time=request.POST.get("start_time"),
                end_date=request.POST.get("end_date"),
                end_time=request.POST.get("end_time"),
                combo_price=request.POST.get("combo_price") or None,
                free_product_id=request.POST.get("free_product") or None,
            )
            if "deal_image" in request.FILES:
                deal.deal_image = request.FILES["deal_image"]
            if "deal_banner" in request.FILES:
                deal.deal_banner = request.FILES["deal_banner"]
            deal.save()
            product_ids = request.POST.getlist("products")
            if product_ids:
                deal.products.set(Food.objects.filter(id__in=product_ids))
            messages.success(request, "Deal created successfully.")
            return redirect("users:deal_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "admin/deal_form.html", {"active_page": "deals", "products": products})


@staff_member_required
def deal_edit(request, pk):
    deal = get_object_or_404(TodayDeal, pk=pk)
    products = Food.objects.all()
    if request.method == "POST":
        try:
            deal.title = request.POST.get("title")
            deal.description = request.POST.get("description", "")
            deal.is_active = request.POST.get("is_active") == "1"
            deal.start_date = request.POST.get("start_date")
            deal.start_time = request.POST.get("start_time")
            deal.end_date = request.POST.get("end_date")
            deal.end_time = request.POST.get("end_time")
            deal.combo_price = request.POST.get("combo_price") or None
            deal.free_product_id = request.POST.get("free_product") or None
            if "deal_image" in request.FILES:
                deal.deal_image = request.FILES["deal_image"]
            if "deal_banner" in request.FILES:
                deal.deal_banner = request.FILES["deal_banner"]
            deal.save()
            product_ids = request.POST.getlist("products")
            if product_ids:
                deal.products.set(Food.objects.filter(id__in=product_ids))
            else:
                deal.products.clear()
            messages.success(request, "Deal updated successfully.")
            return redirect("users:deal_list")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "admin/deal_form.html", {"deal": deal, "active_page": "deals", "products": products})


@staff_member_required
def deal_detail(request, pk):
    deal = get_object_or_404(TodayDeal, pk=pk)
    deal_products = deal.products.all()
    original_total = sum(float(p.price) for p in deal_products)
    if deal.free_product:
        original_total += float(deal.free_product.price)
    savings = 0
    if deal.combo_price and original_total > 0:
        savings = original_total - float(deal.combo_price)
        if savings < 0:
            savings = 0
    return render(request, "admin/deal_detail.html", {
        "deal": deal,
        "deal_products": deal_products,
        "original_total": original_total,
        "savings": savings,
        "active_page": "deals",
    })


@staff_member_required
def deal_delete(request, pk):
    deal = get_object_or_404(TodayDeal, pk=pk)
    if request.method == "POST":
        try:
            deal.delete()
            messages.success(request, "Deal deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return redirect("users:deal_list")


# =========================
# PUBLIC DEAL VIEWS
# =========================
def public_deal_detail(request, pk):
    deal = get_object_or_404(TodayDeal, pk=pk)
    if not deal.is_active:
        return render(request, "food-delivery/deal_detail.html", {"deal": None, "error": "This deal is no longer active."})
    deal_products = deal.products.all()
    original_total = sum(float(p.price) for p in deal_products)
    if deal.free_product:
        original_total += float(deal.free_product.price)
    savings = 0
    if deal.combo_price and original_total > 0:
        savings = original_total - float(deal.combo_price)
        if savings < 0:
            savings = 0
    return render(request, "food-delivery/deal_detail.html", {
        "deal": deal,
        "deal_products": deal_products,
        "original_total": original_total,
        "savings": savings,
    })


@login_required(login_url='food-delivery:food_delivery_login')
def deal_checkout(request, pk):
    deal = get_object_or_404(TodayDeal, pk=pk)
    if not deal.is_active:
        messages.error(request, "This deal is no longer active.")
        return redirect("/")
    if request.method == "POST":
        deal_products = list(deal.products.all())
        if deal.free_product:
            deal_products.append(deal.free_product)
        cart_data = []
        for p in deal_products:
            cart_data.append({
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "image": p.image.url if p.image else "/static/food-delivery/img/item1.png",
                "qty": 1,
            })
        request.session["deal_checkout_cart"] = json.dumps(cart_data)
        request.session["deal_checkout_id"] = deal.id
        return redirect("users:food_delivery_restaurant_detail")
    return redirect("users:public_deal_detail", pk=pk)


@csrf_exempt
def clear_deal_cart(request):
    if request.method == "POST":
        request.session.pop("deal_checkout_cart", None)
        request.session.pop("deal_checkout_id", None)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)
