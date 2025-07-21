from django.urls import path
from bankapi.views import *

urlpatterns = [
    path('signup/', signup),
    path('logout/', logout_view),
    path('send-otp/', send_otp),
    path('verify-otp/', verify_otp),
    path('reset-password/', reset_password),
    path('balance/', get_balance),
    path('transfer/', make_transaction),
    path('statements/', account_statements),
    path('download-statements/', download_statements),
    path('save-profile/', save_profile),
]
