from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'first_name',
        'last_name',
        'pancard',
        'aadhaar',
        'address_line1',
        'pin_code',
        'district',
        'state',
        'gender',
    )
    search_fields = ('user__username', 'pancard', 'aadhaar')