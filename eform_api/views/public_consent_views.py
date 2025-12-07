from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import OrderingFilter
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import IntegrityError

from ..models import (
    TattooArtist,
    Customer,
    CustomerConsent,
    ConsentEntryToken,
    ConsentAccessLog,
)

from ..serializers import (
    CustomerConsentReadSerializer,
    CustomerConsentWriteSerializer,
)


# -------------------------
# ヘルパー: IP取得
# -------------------------
def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


# =========================
# 0. トークン発行 API（認証必須）
# =========================

class CreateConsentEntryTokenSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=100, required=False, allow_blank=True)
    # 🔥 追加：true のときは「既存有効トークンを無効化して新規発行」する
    rotate = serializers.BooleanField(required=False, default=False)


class PublicConsentEntryTokenCreateView(APIView):
    """
    彫師が QR 用トークンを発行する API
    /api/consent/public/token/create/

    基本方針
    - デフォルト: すでに有効なトークンがあれば再利用
    - rotate=true: 既存の is_active=True を無効化し、新しいトークンを発行
                   → 古いQRコードは is_valid() で弾かれる
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateConsentEntryTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # ---- ユーザーに紐づく TattooArtist が存在するか確認 ----
        try:
            artist = TattooArtist.objects.get(user=request.user)
        except TattooArtist.DoesNotExist:
            return Response(
                {"detail": "このユーザーには彫師プロフィールが紐付いていません"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rotate = data.get("rotate", False)

        if rotate:
            # 🔥 再発行モード：
            # 既存の有効トークンをすべて無効化してから、新しいトークンを作る
            ConsentEntryToken.objects.filter(
                artist=artist,
                is_active=True,
            ).update(is_active=False)

            token = ConsentEntryToken.objects.create(
                artist=artist,
                label=data.get("label", ""),
                is_active=True,
                expires_at=None,  # 期限なし。運用で is_active=False にして入れ替え
            )

        else:
            # ① すでに有効なトークンがあればそれを再利用
            token = ConsentEntryToken.objects.filter(
                artist=artist,
                is_active=True,
            ).order_by("created_at").first()

            # ② なければ新規発行
            if not token:
                token = ConsentEntryToken.objects.create(
                    artist=artist,
                    label=data.get("label", ""),
                    is_active=True,
                    expires_at=None,
                )
            else:
                # 任意：ラベル更新
                if "label" in data:
                    token.label = data["label"]
                    token.save(update_fields=["label"])

        return Response(
            {
                "token_uuid": str(token.uuid),
                "artist_uuid": str(artist.uuid),
                "label": token.label,
                "expires_at": token.expires_at,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================
# 1. ご新規同意: Entry(Post)
# =========================

class PublicConsentSerializer(serializers.Serializer):
    entry_token = serializers.UUIDField()

    full_name = serializers.CharField(max_length=255)
    gender = serializers.CharField(max_length=16)
    birth_date = serializers.CharField(max_length=10)
    prefecture = serializers.CharField(max_length=64)
    city = serializers.CharField(max_length=64)
    phone_number = serializers.CharField(max_length=32)

    consent_version = serializers.CharField(max_length=64)
    privacy_agreement_version = serializers.CharField(max_length=64)
    signature = serializers.CharField()


class PublicConsentEntryView(APIView):
    """
    ログイン不要のお客さん用 同意書エントリ
    /api/consent/public/entry/
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PublicConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # ---- 1. トークン確認 ----
        try:
            token = ConsentEntryToken.objects.select_related("artist__user").get(
                uuid=data["entry_token"]
            )
        except ConsentEntryToken.DoesNotExist:
            return Response({"detail": "entry_token が不正です"}, status=400)

        if not token.is_valid():
            return Response({"detail": "このQRコードは現在使用できません。"}, status=400)

        artist = token.artist
        user = artist.user

        # ---- 2. 顧客情報検索または作成 ----
        customer = Customer.objects.filter(
            user=user,
            phone_number=data["phone_number"],
        ).first()

        birth_str = str(data["birth_date"] or "")

        if customer is None:
            customer = Customer.objects.create(
                user=user,
                full_name=data["full_name"],
                gender=data["gender"],
                birth_date=birth_str,
                prefecture=data["prefecture"],
                city=data["city"],
                phone_number=data["phone_number"],
                tattooist=artist.artist_name,
            )
        else:
            customer.full_name = data["full_name"]
            customer.gender = data["gender"]
            customer.birth_date = birth_str
            customer.prefecture = data["prefecture"]
            customer.city = data["city"]
            customer.phone_number = data["phone_number"]
            customer.tattooist = artist.artist_name
            customer.save()

        # ---- 3. 同意履歴の作成 ----
        now = timezone.now()
        try:
            consent = CustomerConsent.objects.create(
                customer=customer,
                consent_version=data["consent_version"],
                signed_at=now,
                signature=data["signature"],
                privacy_agreement_version=data["privacy_agreement_version"],
                privacy_agreement_agreed_at=now,
            )
        except IntegrityError:
            consent = CustomerConsent.objects.get(
                customer=customer,
                consent_version=data["consent_version"],
            )

        # ---- 4. アクセスログ ----
        ConsentAccessLog.objects.create(
            token=token,
            ip_address=get_client_ip(request) or "0.0.0.0",
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
            customer_phone=data["phone_number"],
        )

        token.last_used_at = now
        token.save(update_fields=["last_used_at"])

        return Response(
            {
                "customer_uuid": str(customer.uuid),
                "consent_uuid": str(consent.uuid),
            },
            status=201,
        )


# =========================
# 2. 電話＋生年月日 lookup(GET)
# =========================

class PublicLookupSerializer(serializers.Serializer):
    entry_token = serializers.UUIDField()
    phone = serializers.CharField(max_length=32)
    birth_date = serializers.CharField(max_length=10)


class PublicLookupCustomerByPhoneView(APIView):
    """
    /api/consent/public/lookup-by-phone/
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        serializer = PublicLookupSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            token = ConsentEntryToken.objects.select_related("artist__user").get(
                uuid=data["entry_token"]
            )
        except ConsentEntryToken.DoesNotExist:
            return Response({"detail": "entry_token が不正です"}, status=400)

        if not token.is_valid():
            return Response({"detail": "このQRコードは現在使用できません。"}, status=400)

        artist = token.artist
        user = artist.user

        qs = Customer.objects.filter(
            user=user,
            phone_number=data["phone"],
            birth_date=data["birth_date"],
        )

        return Response(
            [{"uuid": str(c.uuid), "full_name": c.full_name} for c in qs],
            status=200,
        )


# =========================
# 3. 再同意: renew(Post)
# =========================

class PublicConsentRenewSerializer(serializers.Serializer):
    entry_token = serializers.UUIDField()
    customer_uuid = serializers.UUIDField()
    consent_version = serializers.CharField(max_length=64)
    privacy_agreement_version = serializers.CharField(max_length=64)
    signature = serializers.CharField()


class PublicConsentRenewView(APIView):
    """
    /api/consent/public/renew/
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PublicConsentRenewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 1) トークン確認
        try:
            token = ConsentEntryToken.objects.select_related("artist__user").get(
                uuid=data["entry_token"]
            )
        except ConsentEntryToken.DoesNotExist:
            return Response({"detail": "entry_token が不正です"}, status=400)

        if not token.is_valid():
            return Response({"detail": "このQRコードは現在使用できません。"}, status=400)

        # 2) 顧客確認
        try:
            customer = Customer.objects.select_related("user").get(
                uuid=data["customer_uuid"]
            )
        except Customer.DoesNotExist:
            return Response({"detail": "customer_uuid が不正です"}, status=400)

        # 3) token の artist と 顧客の user が一致するか
        if customer.user_id != token.artist.user_id:
            return Response(
                {"detail": "このQRコードからはこのお客様の再同意は行えません。"},
                status=400,
            )

        # 4) 再同意レコード作成
        now = timezone.now()
        consent = CustomerConsent.objects.create(
            customer=customer,
            consent_version=data["consent_version"],
            signed_at=now,
            signature=data["signature"],
            privacy_agreement_version=data["privacy_agreement_version"],
            privacy_agreement_agreed_at=now,
        )

        # 5) アクセスログ & 最終利用日時更新
        ConsentAccessLog.objects.create(
            token=token,
            ip_address=get_client_ip(request) or "0.0.0.0",
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
            customer_phone=customer.phone_number,
        )
        token.last_used_at = now
        token.save(update_fields=["last_used_at"])

        return Response(
            {
                "customer_uuid": str(customer.uuid),
                "consent_uuid": str(consent.uuid),
            },
            status=201,
        )


# =========================
# 4. トークン有効性チェック(GET)
# =========================

class PublicEntryTokenStatusView(APIView):
    """
    /api/consent/public/token/<uuid>/
    """
    permission_classes = [AllowAny]

    def get(self, request, token_uuid, *args, **kwargs):
        try:
            token = ConsentEntryToken.objects.select_related("artist").get(
                uuid=token_uuid
            )
        except ConsentEntryToken.DoesNotExist:
            return Response(
                {"valid": False, "reason": "not_found", "artist": None},
                status=200,
            )

        if not token.is_valid():
            return Response(
                {"valid": False, "reason": "inactive_or_expired", "artist": None},
                status=200,
            )

        artist = token.artist

        return Response(
            {
                "valid": True,
                "reason": None,
                "artist": {
                    "uuid": str(artist.uuid),
                    "artist_name": artist.artist_name,
                    "studio_name": artist.studio_name,
                },
            },
            status=200,
        )


# ------------------------------
# 1(3).顧客の同意履歴 ViewSet
# ------------------------------


class CustomerConsentViewSet(viewsets.ModelViewSet):
    """
    顧客の同意履歴 ViewSet

    - 自分の顧客（customer.user == request.user）に限定
    - ?customer=UUID / ?customer__uuid=UUID で顧客ごとに絞り込み
    - ?active_only=1 / true / True で is_active=True の顧客分だけに絞る
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

        # 1. 自分の顧客に限定
        qs = qs.filter(customer__user=self.request.user)

        # 2. active_only パラメータがあれば is_active=True の顧客だけに絞る
        active_only = self.request.query_params.get('active_only')
        if active_only in ('1', 'true', 'True'):
            qs = qs.filter(customer__is_active=True)

        # 3. フロントの ?customer=XXX と、django-filter 用の ?customer__uuid=XXX の両方を許容
        customer_uuid = (
            self.request.query_params.get('customer')
            or self.request.query_params.get('customer__uuid')
        )
        if customer_uuid:
            qs = qs.filter(customer__uuid=customer_uuid)

        # ordering はクラス属性 + OrderingFilter に任せる
        return qs
