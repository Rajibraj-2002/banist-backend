from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Account, Transaction, UserProfile

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    new_password = serializers.CharField()

class OTPRequestSerializer(serializers.Serializer):
    username = serializers.CharField()

class OTPVerifySerializer(serializers.Serializer):
    username = serializers.CharField()
    code = serializers.CharField()

class TransferSerializer(serializers.Serializer):
    to = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['balance']

class TransactionSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.user.username')
    receiver = serializers.CharField(source='receiver.user.username')

    class Meta:
        model = Transaction
        fields = ['sender', 'receiver', 'amount', 'timestamp']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'photo', 'first_name', 'middle_name', 'last_name', 'pancard',
            'aadhaar', 'address_line1', 'pin_code', 'district', 'state', 'gender'
        ]


