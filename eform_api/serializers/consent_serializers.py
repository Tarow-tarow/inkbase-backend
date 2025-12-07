# backend/eform_api/serializers/consent_serializers.py
from rest_framework import serializers
from ..models import CustomerConsent, Customer


# ----------------------------------------
# 1. 同意書PDF生成時の簡易顧客情報
# ----------------------------------------
class CustomerSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['uuid', 'full_name', 'birth_date']


# ----------------------------------------
# 1.5 同意履歴一覧用の軽量顧客サマリ
#    ※ merged_into_uuid / is_active を含む
# ----------------------------------------
class CustomerSummarySerializer(serializers.ModelSerializer):
    merged_into_uuid = serializers.UUIDField(
        source='merged_into.uuid',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Customer
        fields = [
            'uuid',
            'full_name',
            'last_name',
            'first_name',
            'is_active',        # ← この顧客が現在有効か
            'merged_into_uuid', # ← 統合先の UUID（なければ null）
        ]


# ----------------------------------------
# 2. 同意履歴 GET（表示用）
#    ※ is_merged を backend で判定
#    ※ merged_into_uuid も明示的に返す
# ----------------------------------------
class CustomerConsentReadSerializer(serializers.ModelSerializer):
    customer = CustomerSummarySerializer(read_only=True)

    # 🔥 バッジ判定のための追加フィールド
    is_merged = serializers.SerializerMethodField()
    merged_into_uuid = serializers.SerializerMethodField()

    class Meta:
        model = CustomerConsent
        fields = [
            'uuid',
            'customer',

            'consent_version',
            'signed_at',
            'signature',
            'privacy_agreement_version',
            'privacy_agreement_agreed_at',
            'visit_date',

            'is_active',
            'created_at',
            'updated_at',

            # snapshot 系
            'customer_uuid_snapshot',
            'customer_name_snapshot',
            'customer_birth_date_snapshot',
            'customer_phone_snapshot',

            # 🔥 バックエンド側が返す統合情報
            'is_merged',
            'merged_into_uuid',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    # ----------------------------------------------------
    # 🔥 統合判定（マージ元かどうか）
    # ----------------------------------------------------
    def get_is_merged(self, obj):
        """
        この同意が紐づく customer が merged_into を持っていれば統合済み。
        snapshot と現在の顧客UUIDを比較する必要はない。
        """
        c = getattr(obj, 'customer', None)
        if not c:
            return False
        return bool(c.merged_into_id)

    def get_merged_into_uuid(self, obj):
        """
        統合先の UUID を返す。
        """
        c = getattr(obj, 'customer', None)
        if not c:
            return None
        merged_into = getattr(c, 'merged_into', None)
        if not merged_into:
            return None
        return str(merged_into.uuid)


# ----------------------------------------
# 3. 同意履歴 POST / PUT 用
# ----------------------------------------
class CustomerConsentWriteSerializer(serializers.ModelSerializer):
    customer = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Customer.objects.all(),
    )

    class Meta:
        model = CustomerConsent
        fields = [
            'uuid',
            'customer',
            'consent_version',
            'signed_at',
            'signature',
            'privacy_agreement_version',
            'privacy_agreement_agreed_at',
            'visit_date',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']
