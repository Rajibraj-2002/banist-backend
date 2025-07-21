from tokenize import TokenError
from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny 
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from datetime import timedelta
from .models import Account, Transaction, OTP, UserProfile
from .serializers import *

# ✅ Utility to generate 6-digit OTP
def generate_otp():
    import random
    return str(random.randint(100000, 999999))

# ✅ Twilio SMS
def send_sms_otp(phone, otp_code):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=f"Your OTP is {otp_code}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Account.objects.create(user=user)
        return Response({'message': 'Signup successful'})
    print(serializer.errors)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    serializer = OTPRequestSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        try:
            user = User.objects.get(username=username)
            otp_code = generate_otp()
            OTP.objects.create(user=user, code=otp_code)

            send_mail(
                'Your Bankist OTP',
                f'Your OTP is {otp_code}. Valid for 5 minutes.',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False
            )

            if hasattr(user, 'profile') and user.profile.phone:
                send_sms_otp(user.profile.phone, otp_code)

            return Response({'message': 'OTP sent successfully'})

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def verify_otp(request):
    serializer = OTPVerifySerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        code = serializer.validated_data['code']
        try:
            user = User.objects.get(username=username)
            otp_obj = OTP.objects.filter(user=user, code=code).last()
            if otp_obj and timezone.now() - otp_obj.created_at < timedelta(minutes=5):
                return Response({'message': 'OTP verified'})
            else:
                return Response({'error': 'Invalid or expired OTP'}, status=400)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_password(request):
    username = request.user.username
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    user = request.user
    if not user.check_password(current_password):
        return Response({'error': 'Current password is incorrect'}, status=400)

    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password reset successful'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    serializer = UserProfileSerializer(profile, data=request.data, context={'request': request}, partial=True)

    if serializer.is_valid():
        serializer.save()
        photo_url = request.build_absolute_uri(profile.photo.url) if profile.photo else ''
        return Response({'message': 'Profile saved successfully', 'photo_url': photo_url})
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_balance(request):
    account = Account.objects.get(user=request.user)
    serializer = AccountSerializer(account)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_transaction(request):
    serializer = TransferSerializer(data=request.data)
    if serializer.is_valid():
        sender = Account.objects.get(user=request.user)
        receiver_username = serializer.validated_data['to']
        amount = serializer.validated_data['amount']

        try:
            receiver_user = User.objects.get(username=receiver_username)
            receiver = Account.objects.get(user=receiver_user)
            if sender.balance < amount:
                return Response({'error': 'Insufficient funds'}, status=400)
            sender.balance -= amount
            receiver.balance += amount
            sender.save()
            receiver.save()
            Transaction.objects.create(sender=sender, receiver=receiver, amount=amount)
            return Response({'message': 'Transaction successful'})
        except User.DoesNotExist:
            return Response({'error': 'Receiver not found'}, status=404)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_statements(request):
    account = Account.objects.get(user=request.user)
    sent = Transaction.objects.filter(sender=account)
    received = Transaction.objects.filter(receiver=account)
    sent_data = TransactionSerializer(sent, many=True).data
    received_data = TransactionSerializer(received, many=True).data
    return Response({'sent': sent_data, 'received': received_data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_statements(request):
    username = request.GET.get('username', 'User')
    balance = request.GET.get('balance', '0.00')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="statement_{username}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, 800, f"Account Statement")
    p.setFont("Helvetica", 14)
    p.drawString(50, 770, f"User: {username}")
    p.drawString(50, 750, f"Current Balance: ₹{balance}")
    p.drawString(50, 720, f"Generated on: {request._request.META.get('HTTP_DATE', '')}")
    p.drawString(50, 690, "Note: Detailed transactions available on dashboard.")
    p.showPage()
    p.save()
    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    from rest_framework_simplejwt.tokens import RefreshToken, TokenError

    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({"message": "Logout successful"}, status=200)
    except TokenError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        return Response({"error": "Something went wrong."}, status=500)
