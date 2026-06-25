import uuid
import io
import qrcode
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone as tz_utils
from django.utils.crypto import get_random_string
from django.conf import settings
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_operator = models.BooleanField(default=False)
    is_kitchen = models.BooleanField(default=False)
    timezone = models.CharField(max_length=100, default="UTC")
    date_joined = models.DateTimeField(default=tz_utils.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()


class RestaurantTable(models.Model):
    table_no = models.IntegerField(unique=True)
    qr_code_image = models.ImageField(upload_to="table_qrcodes/", blank=True, null=True)
    qr_token = models.CharField(max_length=64, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.qr_token:
            self.qr_token = get_random_string(32)
        super().save(*args, **kwargs)

    def generate_qr_code(self, request=None):
        domain = "http://localhost:8000"
        if request:
            domain = f"{request.scheme}://{request.get_host()}"
        url = f"{domain}/menu/?table={self.table_no}&token={self.qr_token}"
        qr = qrcode.make(url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        filename = f"table_{self.table_no}_qr.png"
        self.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=False)

    def __str__(self):
        return f"Table {self.table_no}"


class Invoice(models.Model):
    uuid_token = models.CharField(max_length=64, unique=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    table_no = models.IntegerField(null=True, blank=True)
    customer_session_id = models.CharField(max_length=100, blank=True, null=True)
    invoice_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_timezone = models.CharField(max_length=100, default="UTC")
    qr_code_image = models.ImageField(upload_to="invoice_qrcodes/", blank=True, null=True)
    is_loyalty_payment = models.BooleanField(default=False, help_text="Paid using loyalty points")
    loyalty_points_used = models.IntegerField(default=0, help_text="Loyalty points used for payment")
    loyalty_points_earned = models.IntegerField(default=0, help_text="Loyalty points earned from this order")
    loyalty_points_processed = models.BooleanField(default=False, help_text="Prevent duplicate point processing")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.uuid_token:
            self.uuid_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def generate_qr_code(self, request=None):
        domain = "http://localhost:8000"
        if request:
            domain = f"{request.scheme}://{request.get_host()}"
        secure_url = f"{domain}/users/invoice/{self.uuid_token}/verify/"
        qr = qrcode.make(secure_url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        filename = f"invoice_{self.invoice_number}_qr.png"
        self.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=False)

    def __str__(self):
        return self.invoice_number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.product_name


class KitchenOrder(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("preparing", "Preparing"),
        ("ready", "Ready"),
        ("delivered", "Delivered"),
    )

    uuid_token = models.CharField(max_length=64, unique=True, blank=True)
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="kitchen_order")
    order_number = models.CharField(max_length=30, unique=True)
    table_no = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.uuid_token:
            self.uuid_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class KitchenOrderItem(models.Model):
    order = models.ForeignKey(KitchenOrder, on_delete=models.CASCADE, related_name="items")
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()


class LoyaltyCard(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('BLOCKED', 'Blocked'),
    ]

    card_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loyalty_cards',
        null=True, blank=True
    )
    total_points = models.IntegerField(default=0)
    used_points = models.IntegerField(default=0)
    remaining_points = models.IntegerField(default=0)
    qr_token = models.CharField(max_length=64, unique=True, blank=True)
    qr_code_image = models.ImageField(upload_to='loyalty_qr/', blank=True, null=True)
    card_pdf = models.FileField(upload_to='loyalty_cards/pdf/', blank=True, null=True)
    card_image = models.ImageField(upload_to='loyalty_cards/images/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    first_card_popup_shown = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loyalty_cards_loyaltycard'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.card_number:
            while True:
                cnum = f"LC{get_random_string(10).upper()}"
                if not LoyaltyCard.objects.filter(card_number=cnum).exists():
                    self.card_number = cnum
                    break
        if not self.qr_token:
            self.qr_token = get_random_string(32)
        self.remaining_points = self.total_points - self.used_points
        super().save(*args, **kwargs)
        if is_new and self.total_points == 0:
            self.total_points = 20
            self.remaining_points = 20
            self.save(update_fields=['total_points', 'remaining_points'])
            LoyaltyTransaction.objects.create(
                card=self,
                order_number="WELCOME",
                earned_points=20,
                redeemed_points=0,
                remaining_balance=20,
                transaction_type='EARN'
            )

    def add_points(self, points, order_number=""):
        if points < 0:
            raise ValueError("Points cannot be negative")
        self.total_points += points
        self.remaining_points = self.total_points - self.used_points
        self.save()
        LoyaltyTransaction.objects.create(
            card=self,
            order_number=order_number,
            earned_points=points,
            redeemed_points=0,
            remaining_balance=self.remaining_points,
            transaction_type='EARN'
        )

    def redeem_points(self, points, order_number=""):
        if points < 0:
            raise ValueError("Points cannot be negative")
        if self.remaining_points < points:
            raise ValueError("Insufficient points balance")
        self.used_points += points
        self.remaining_points = self.total_points - self.used_points
        self.save()
        LoyaltyTransaction.objects.create(
            card=self,
            order_number=order_number,
            earned_points=0,
            redeemed_points=points,
            remaining_balance=self.remaining_points,
            transaction_type='REDEEM'
        )

    def generate_qr_data(self):
        return {
            "token": self.qr_token,
            "card": self.card_number,
            "customer": self.user.id if self.user else 0,
        }

    def __str__(self):
        return f"Loyalty Card {self.card_number}"


class LoyaltyTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('EARN', 'Earn'),
        ('REDEEM', 'Redeem'),
    ]

    card = models.ForeignKey(LoyaltyCard, on_delete=models.CASCADE, related_name='transactions')
    order_number = models.CharField(max_length=50, blank=True, null=True)
    earned_points = models.IntegerField(default=0)
    redeemed_points = models.IntegerField(default=0)
    remaining_balance = models.IntegerField(default=0)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loyalty_cards_loyaltytransaction'

    def __str__(self):
        return f"{self.transaction_type} - {self.card.card_number}"
