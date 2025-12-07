from rest_framework import permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import UserAgreement
from ..serializers import (
    UserAgreementSerializer
)

# ------------------------------
# 1(12). ユーザー用同意履歴のAPI
# ------------------------------

class UserAgreementCreateView(generics.CreateAPIView):
    serializer_class = UserAgreementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# ------------------------------
# 2. ユーザーの同意状況を返すAPI
# ------------------------------

class UserAgreementStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        exists = UserAgreement.objects.filter(user=request.user).exists()
        return Response({'agreed': exists})
