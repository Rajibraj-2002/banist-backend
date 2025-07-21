from django.shortcuts import render

# Create your views here.

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from bankapi.models import Account, Transaction, UserProfile
from django.utils import timezone
from datetime import timedelta
from bankapi.models import UserProfile  # Add this import if not already

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    user = request.user
    account = Account.objects.get(user=user)

     # Get user profile and photo URL
    try:
        profile = UserProfile.objects.get(user=user)
        photo_url = request.build_absolute_uri(profile.photo.url) if profile.photo else None
        profile_data = {
            'photo_url': photo_url,
            'first_name': profile.first_name,
            'middle_name': profile.middle_name,
            'last_name': profile.last_name,
            'pancard': profile.pancard,
            'aadhaar': profile.aadhaar,
            'address_line1': profile.address_line1,
            'pin_code': profile.pin_code,
            'district': profile.district,
            'state': profile.state,
            'gender': profile.gender,
        }
    except UserProfile.DoesNotExist:
        # photo_url = None
        profile_data = {}

    # Last 5 transactions (both sent and received)
    recent_transactions = Transaction.objects.filter(
        sender=account
    ).union(
        Transaction.objects.filter(receiver=account)
    ).order_by('-timestamp')[:5]

    transactions_data = [
        {
            'timestamp': tx.timestamp,
            'type': 'Sent' if tx.sender == account else 'Received',
            'user': tx.receiver.user.username if tx.sender == account else tx.sender.user.username,
            'amount': tx.amount
        } for tx in recent_transactions
    ]

    # Summary
    summary_data = {
        # 'photo_url': photo_url,
        'username': user.username,
        'email': user.email,
        'balance': account.balance,
        'profile': profile_data,
        'recent_transactions': transactions_data,
    }
    return Response(summary_data)
