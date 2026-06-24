from django.db import models
from django.conf import settings
from django.utils import timezone as tz_utils
from django.utils.crypto import get_random_string
import uuid


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
    card_pdf = models.FileField(upload_to='loyalty_cards/pdf/', blank=True, null=True)
    card_image = models.ImageField(upload_to='loyalty_cards/images/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
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
            "card_token": self.qr_token,
            "customer_id": self.user.id if self.user else 0,
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

    def __str__(self):
        return f"{self.transaction_type} - {self.card.card_number}"
