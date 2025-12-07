from rest_framework import serializers
from ..models import Customer, CustomerConsent
from .consent_serializers import CustomerConsentReadSerializer, CustomerConsentWriteSerializer
from ..utils import normalize_phone_number

# ----------------------------------------
# 1(4).顧客モデル Customer Serializer
# ----------------------------------------


class CustomerSerializer(serializers.ModelSerializer):
    consents = CustomerConsentReadSerializer(many=True, read_only=True)
    avatar_url = serializers.CharField(
        allow_blank=True, allow_null=True, required=False)
    birth_date = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['uuid', 'user', 'created_at', 'updated_at']

    def validate_phone_number(self, value):
        return normalize_phone_number(value)

# ----------------------------------------
# 2(5).顧客簡易追加 CustomerEasyCreateSerializer
# ----------------------------------------


class CustomerEasyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['uuid', 'user', 'full_name', 'gender',
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'user', 'created_at', 'updated_at']
        extra_kwargs = {
            'birth_date': {'required': False, 'allow_null': True},
            'prefecture': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'phone_number': {'required': False, 'allow_blank': True},
            'avatar_url': {'required': False, 'allow_blank': True},
            'tattooist': {'required': False, 'allow_blank': True},
        }

# ----------------------------------------
# 3(6).顧客詳細ページ 顧客情報・同意情報表示用 CustomerDetailSerializer
# ----------------------------------------


class CustomerDetailSerializer(serializers.ModelSerializer):
    consents = CustomerConsentReadSerializer(
        many=True, read_only=True)  # ✅ 表示用はRead用Serializerで
    latest_consent = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['uuid', 'user', 'created_at', 'updated_at']

    def get_latest_consent(self, obj):
        latest = obj.consents.order_by('-signed_at').first()
        if latest:
            return CustomerConsentReadSerializer(latest).data
        return None
