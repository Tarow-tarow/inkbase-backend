# backend/eform_api/views/token_views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# ------------------------------
# 1. Djangoの標準ユーザー認証（username + password）
# ------------------------------


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
