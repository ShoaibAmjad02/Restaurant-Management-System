import json
from django.db import models
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone as tz_utils
from django.db.models import Sum, Q
from .models import LoyaltyCard, LoyaltyTransaction
from .utils import generate_loyalty_card_pdf, generate_loyalty_card_image, generate_qr_code_image


@login_required
def my_loyalty_card(request):
    card = LoyaltyCard.objects.filter(user=request.user).first()
    if not card:
        card = LoyaltyCard.objects.create(user=request.user, status='ACTIVE')
    # Ensure QR code image exists; generate if missing
    qr_ok = card.qr_code_image and card.qr_code_image.storage.exists(card.qr_code_image.name)
    if not qr_ok:
        try:
            generate_qr_code_image(card)
        except Exception:
            pass
    # Ensure PDF and PNG exist; generate if missing (regenerates with current QR)
    if not card.card_pdf or not card.card_image:
        try:
            generate_loyalty_card_pdf(card)
            generate_loyalty_card_image(card)
        except Exception:
            pass
    # Show welcome message only on first visit, then set flag
    show_welcome = not card.first_card_popup_shown
    if show_welcome:
        card.first_card_popup_shown = True
        card.save(update_fields=['first_card_popup_shown'])
    transactions = LoyaltyTransaction.objects.filter(card=card).order_by('-created_at')
    return render(request, 'loyalty_cards/my_card.html', {
        'card': card,
        'transactions': transactions,
        'show_welcome': show_welcome,
    })


@login_required
def download_card_pdf(request, card_number):
    card = get_object_or_404(LoyaltyCard, card_number=card_number, user=request.user)
    # Ensure QR exists before generating PDF
    if not card.qr_code_image or not card.qr_code_image.storage.exists(card.qr_code_image.name):
        generate_qr_code_image(card)
    if not card.card_pdf:
        generate_loyalty_card_pdf(card)
    return FileResponse(card.card_pdf, as_attachment=True, filename=f"loyalty_card_{card.card_number}.pdf")


@login_required
def download_card_image(request, card_number):
    card = get_object_or_404(LoyaltyCard, card_number=card_number, user=request.user)
    if not card.qr_code_image or not card.qr_code_image.storage.exists(card.qr_code_image.name):
        generate_qr_code_image(card)
    if not card.card_image:
        generate_loyalty_card_image(card)
    return FileResponse(card.card_image, as_attachment=True, filename=f"loyalty_card_{card.card_number}.png")


@csrf_exempt
def verify_qr_token(request, qr_token):
    if request.method == 'GET':
        card = LoyaltyCard.objects.filter(qr_token=qr_token).first()
        if not card:
            return JsonResponse({'valid': False, 'error': 'Invalid QR token'}, status=404)
        return JsonResponse({
            'valid': True,
            'card_number': card.card_number,
            'customer': card.user.name if card.user else 'Customer',
        })
    return JsonResponse({'valid': False}, status=405)


@csrf_exempt
@login_required
def loyalty_checkout_validate(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            total_amount = float(data.get('total_amount', 0))
            card = LoyaltyCard.objects.filter(user=request.user, status='ACTIVE').first()
            if not card:
                return JsonResponse({'can_pay': False, 'error': 'No active loyalty card found'})
            if card.remaining_points < total_amount:
                return JsonResponse({
                    'can_pay': False,
                    'error': f'Insufficient Loyalty Points. You have {card.remaining_points} points but need {int(total_amount)}.',
                    'available_points': card.remaining_points,
                })
            return JsonResponse({
                'can_pay': True,
                'available_points': card.remaining_points,
                'points_needed': int(total_amount),
                'card_number': card.card_number,
            })
        except Exception as e:
            return JsonResponse({'can_pay': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)


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

    return render(request, 'loyalty_cards/admin_list.html', {
        'cards': cards,
        'search': search,
        'status_filter': status_filter,
    })


@staff_member_required
def admin_loyalty_detail(request, card_number):
    card = get_object_or_404(LoyaltyCard, card_number=card_number)
    transactions = LoyaltyTransaction.objects.filter(card=card).order_by('-created_at')
    return render(request, 'loyalty_cards/admin_detail.html', {
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
    return redirect('loyalty_cards:admin_loyalty_detail', card_number=card.card_number)


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
    return redirect('loyalty_cards:admin_loyalty_detail', card_number=card.card_number)


@staff_member_required
def admin_loyalty_reports(request):
    total_cards = LoyaltyCard.objects.count()
    active_cards = LoyaltyCard.objects.filter(status='ACTIVE').count()
    blocked_cards = LoyaltyCard.objects.filter(status='BLOCKED').count()
    total_earned = LoyaltyCard.objects.aggregate(total=Sum('total_points'))['total'] or 0
    total_redeemed = LoyaltyCard.objects.aggregate(total=Sum('used_points'))['total'] or 0
    total_remaining = LoyaltyCard.objects.aggregate(total=models.Sum('remaining_points'))['total'] or 0

    from megaone.users.models import Invoice
    loyalty_revenue = Invoice.objects.filter(is_loyalty_payment=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    context = {
        'total_cards': total_cards,
        'active_cards': active_cards,
        'blocked_cards': blocked_cards,
        'total_earned': total_earned,
        'total_redeemed': total_redeemed,
        'total_remaining': total_remaining,
        'loyalty_revenue': loyalty_revenue,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'loyalty_cards/admin_reports.html', context)


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
