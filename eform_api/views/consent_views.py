from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.exceptions import PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from ..models import CustomerConsent
from ..serializers import (
    CustomerConsentReadSerializer,
    CustomerConsentWriteSerializer,
)

# ------------------------------
# 1(3).顧客の同意履歴 ViewSet
# ------------------------------


class CustomerConsentViewSet(viewsets.ModelViewSet):
    """
    顧客の同意履歴 ViewSet

    - 自分の顧客（customer.user == request.user）に限定
    - ?customer=UUID / ?customer__uuid=UUID で顧客ごとに絞り込み
      （統合先UUID指定時は、その顧客に統合された元顧客の履歴も含める）
    - ?active_only=1 / true / True で
        * is_active=True の顧客
        * もしくは is_active=True な顧客に merged_into されている顧客
      の履歴だけに絞る
    """
    queryset = CustomerConsent.objects.select_related('customer')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        'customer__uuid': ['exact'],
    }
    lookup_field = 'uuid'
    ordering_fields = ['signed_at']
    ordering = ['-signed_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CustomerConsentWriteSerializer
        return CustomerConsentReadSerializer  # 一覧・詳細用

    def perform_create(self, serializer):
        """
        作成時に「自分の顧客」かをチェック
        """
        customer = serializer.validated_data['customer']
        if customer.user != self.request.user:
            raise PermissionDenied("この顧客に対する同意は許可されていません。")
        serializer.save()

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # 1. 自分の顧客に限定
        qs = qs.filter(customer__user=user)

        # 2. active_only パラメータがあれば
        #    - そのまま is_active=True の顧客
        #    - もしくは is_active=True な顧客に merged_into されている顧客
        #    の履歴だけに絞る
        active_only = self.request.query_params.get('active_only')
        if active_only in ('1', 'true', 'True'):
            qs = qs.filter(
                Q(customer__is_active=True) |
                Q(
                    customer__merged_into__isnull=False,
                    customer__merged_into__is_active=True,
                )
            )

        # 3. フロントの ?customer=XXX と、
        #    django-filter 用の ?customer__uuid=XXX の両方を許容
        #    さらに、指定された UUID に統合された元顧客の履歴も拾う
        customer_uuid = (
            self.request.query_params.get('customer')
            or self.request.query_params.get('customer__uuid')
        )
        if customer_uuid:
            qs = qs.filter(
                Q(customer__uuid=customer_uuid) |
                Q(customer__merged_into__uuid=customer_uuid)
            )

        # ordering はクラス属性 + OrderingFilter に任せる
        return qs
