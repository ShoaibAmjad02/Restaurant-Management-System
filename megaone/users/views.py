import io
import json
import uuid
import subprocess
import traceback
import qrcode
from django.http import HttpResponse, JsonResponse
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
from .models import User, Invoice, InvoiceItem, KitchenOrder, KitchenOrderItem, RestaurantTable
from apps.loyalty_cards.models import LoyaltyCard

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
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            # Auto-create loyalty card for any customer who doesn't have one
            if not user.is_staff and not getattr(user, "is_kitchen", False):
                from apps.loyalty_cards.models import LoyaltyCard
                from apps.loyalty_cards.utils import generate_qr_code_image, generate_loyalty_card_pdf, generate_loyalty_card_image
                card, created = LoyaltyCard.objects.get_or_create(
                    user=user,
                    defaults={'status': 'ACTIVE'}
                )
                if created or not card.qr_code_image or not card.card_pdf:
                    try:
                        generate_qr_code_image(card)
                        generate_loyalty_card_pdf(card)
                        generate_loyalty_card_image(card)
                    except Exception:
                        pass
                # First-time redirect to loyalty card page (using DB flag)
                if not card.first_card_popup_shown:
                    return redirect("loyalty_cards:my_card")
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
def _create_order_from_cart(cart, request, user=None, payment_method="card", customer_timezone="UTC"):
    table_no = request.session.get("table_no")
    customer_session = request.session.get("customer_session_id") or str(uuid.uuid4())

    subtotal_amount = 0
    for item in cart:
        qty = int(item["qty"])
        price = float(item["price"])
        subtotal_amount += qty * price

    is_loyalty = payment_method == "loyalty"
    tax_pct = 0 if is_loyalty else (5 if payment_method == "card" else 18)
    tax_amount = round(subtotal_amount * tax_pct / 100, 2)
    grand_total = subtotal_amount + tax_amount

    loyalty_points_used = 0
    loyalty_card = None
    if is_loyalty and user:
        try:
            loyalty_card = LoyaltyCard.objects.get(user=user, status='ACTIVE')
            if loyalty_card.remaining_points >= grand_total:
                points_needed = int(grand_total)
                loyalty_points_used = points_needed
        except LoyaltyCard.DoesNotExist:
            pass

    invoice = Invoice.objects.create(
        user=user,
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        payment_method=payment_method,
        customer_timezone=customer_timezone,
        tax_percentage=tax_pct,
        tax_amount=tax_amount,
        subtotal_amount=subtotal_amount,
        total_amount=grand_total,
        table_no=table_no,
        customer_session_id=customer_session,
        is_loyalty_payment=is_loyalty,
        loyalty_points_used=loyalty_points_used,
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
        if not cart:
            return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

        invoice = _create_order_from_cart(cart, request, payment_method=payment_method, customer_timezone=customer_timezone)
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
        if not cart:
            return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

        invoice = _create_order_from_cart(cart, request, user=request.user, payment_method=payment_method, customer_timezone=customer_timezone)
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
        from apps.loyalty_cards.models import LoyaltyCard
        if LoyaltyCard.objects.filter(user=invoice.user).exists():
            loyalty_height = 35 * mm

    header_height = 65 * mm
    item_per_height = 9 * mm
    summary_height = 40 * mm
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

    pdf.setFont("Helvetica", 8)
    pdf.drawString(MARGIN, y, "Subtotal")
    pdf.drawRightString(right, y, f"Rs {sub_amt:.0f}")
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
    # LOYALTY CARD INFO
    # ==========================
    if invoice.user:
        from apps.loyalty_cards.models import LoyaltyCard
        lcard = LoyaltyCard.objects.filter(user=invoice.user).first()
        if lcard:
            y -= 5 * mm
            pdf.setFont("Helvetica-Bold", 7)
            pdf.setFillColor(HexColor("#f59e0b"))
            pdf.drawCentredString(w / 2, y, "LOYALTY CARD")
            pdf.setFillColor(DARK)
            y -= 4 * mm
            pdf.setFont("Helvetica", 6)
            loyalty_fields = [
                ("Card #", lcard.card_number),
                ("Total Points", str(lcard.total_points)),
                ("Used Points", str(lcard.used_points)),
                ("Remaining Points", str(lcard.remaining_points)),
            ]
            for label, val in loyalty_fields:
                pdf.drawString(MARGIN, y, label)
                pdf.drawRightString(right, y, val)
                y -= 3.5 * mm
            if invoice.loyalty_points_earned > 0:
                pdf.drawString(MARGIN, y, "This Order Earned")
                pdf.drawRightString(right, y, f"+{invoice.loyalty_points_earned} pts")
                y -= 3.5 * mm
            if invoice.is_loyalty_payment and invoice.loyalty_points_used > 0:
                pdf.drawString(MARGIN, y, "This Order Used")
                pdf.drawRightString(right, y, f"-{int(invoice.loyalty_points_used)} pts")
                y -= 3.5 * mm
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
    from apps.loyalty_cards.models import LoyaltyCard
    from django.db.models import Sum
    loyalty_cards_count = LoyaltyCard.objects.count()
    loyalty_active = LoyaltyCard.objects.filter(status='ACTIVE').count()
    loyalty_points_earned = LoyaltyCard.objects.aggregate(total=Sum('total_points'))['total'] or 0
    loyalty_points_redeemed = LoyaltyCard.objects.aggregate(total=Sum('used_points'))['total'] or 0

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

            # Auto-earn loyalty points for delivered orders
            if invoice.user and not invoice.loyalty_points_processed:
                from apps.loyalty_cards.models import LoyaltyCard
                card = LoyaltyCard.objects.filter(user=invoice.user, status='ACTIVE').first()
                if card:
                    total_points = 0
                    for inv_item in invoice.items.all():
                        from menu.models import Food
                        food = Food.objects.filter(name=inv_item.product_name).first()
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
