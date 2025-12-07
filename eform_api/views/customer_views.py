# eform_api/views/customer_views.py

from django.db import transaction
from django.utils.timezone import now as timezone_now

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from ..models import (
    Customer,
    CustomerDeleteLog,
    CustomerMergeLog,
    CustomerConsent,
)
from ..serializers import (
    CustomerSerializer,
    CustomerEasyCreateSerializer,
    CustomerConsentWriteSerializer,
    CustomerDetailSerializer,
)
from ..utils import normalize_phone_number


# ------------------------------
# 1.顧客一覧・作成
# ------------------------------
class CustomerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 自分の顧客 かつ is_active=True のみ
        return (
            Customer.objects.filter(
                user=self.request.user,
                is_active=True,
            )
            .order_by("-updated_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ------------------------------
# 2.顧客詳細取得・更新・削除（削除はソフトデリート）
# ------------------------------
class CustomerRetrieveUpdateAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "uuid"

    def get_queryset(self):
        # 詳細も is_active=True に限定
        return Customer.objects.filter(
            user=self.request.user,
            is_active=True,
        )

    def perform_destroy(self, instance: Customer) -> None:
        """
        DELETE /customers/<uuid>/ に対して、
        物理削除ではなく is_active=False にして削除ログを残す。
        """
        instance.is_active = False
        instance.save()

        CustomerDeleteLog.objects.create(
            customer_uuid=instance.uuid,
            performed_by=self.request.user,
            reason="ユーザーによる削除",
        )


# ------------------------------
# 3.簡易登録 POST専用
# ------------------------------
class CustomerEasyCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data.setdefault("birth_date", None)
        data.setdefault("prefecture", "")
        data.setdefault("city", "")
        data.setdefault("phone_number", "")
        data.setdefault("avatar_url", "")
        data.setdefault("tattooist", "")  # 彫師名がnullでエラー出る構成なら

        serializer = CustomerEasyCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------
# 4.電話番号と生年月日で検索（GET）
# ------------------------------
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def lookup_customer_by_phone(request):
    raw_phone = request.GET.get("phone", "")
    normalized_phone = normalize_phone_number(raw_phone)
    birth_date = request.GET.get("birth_date", "")

    customers = Customer.objects.filter(
        phone_number__icontains=normalized_phone,
        user=request.user,
        is_active=True,
    )

    if birth_date:
        customers = customers.filter(birth_date=birth_date)

    serializer = CustomerSerializer(customers, many=True)
    return Response(serializer.data, status=200)


# ------------------------------
# 5.同意登録（submit-consent）
# ------------------------------
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def submit_customer_consent(request):
    data = request.data
    customer_uuid = data.get("customer_uuid")

    try:
        customer = Customer.objects.get(
            uuid=customer_uuid,
            user=request.user,
            is_active=True,
        )
    except Customer.DoesNotExist:
        return Response({"error": "顧客が見つかりません"}, status=404)

    consent_data = {
        "customer": customer.id,
        "consent_version": data.get("consent_version"),
        "signed_at": data.get("agreements_timestamp", timezone_now()),
        "signature": data.get("signature"),
        "privacy_agreement_version": data.get("privacy_agreement_version"),
        "privacy_agreement_agreed_at": data.get(
            "privacy_agreement_agreed_at"
        ),
    }

    serializer = CustomerConsentWriteSerializer(data=consent_data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "同意情報を保存しました",
                "customer_uuid": str(customer.uuid),
            },
            status=201,
        )

    return Response(serializer.errors, status=400)


# ------------------------------
# 6.顧客フィールドマージ用ヘルパー
# ------------------------------
def merge_customer_fields(keep: Customer, merged: Customer, overwrite: bool = False) -> None:
    """
    顧客フィールドのマージポリシー:
    - overwrite=False: keep 側が空の項目だけ merged から補完
    - overwrite=True : merged の値で keep を上書き
    """
    fields = [
        "full_name",
        "last_name",
        "first_name",
        "last_name_kana",
        "first_name_kana",
        "birth_date",
        "prefecture",
        "city",
        "phone_number",
        "instagram_id",
        "notes",
        "skin_type",
        "tattoo_experience",
        "occupation",
        "referrer",
        "mbti",
        "tattooist",
        "avatar_url",
    ]

    for field in fields:
        keep_value = getattr(keep, field, None)
        merged_value = getattr(merged, field, None)

        if overwrite:
            # マージ元に値があるなら上書き
            if merged_value not in (None, "", False):
                setattr(keep, field, merged_value)
        else:
            # keep が空で merged に値があるときだけ補完
            if keep_value in (None, "", False) and merged_value not in (None, "", False):
                setattr(keep, field, merged_value)


# ------------------------------
# 7.顧客マージ（merge-customers）
# ------------------------------
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def merge_customers(request):
    """
    顧客マージAPI:
    - keep_uuid: 残す顧客
    - merged_uuid: 吸収される顧客
    - overwrite: True の場合、merged の値で keep を上書き
    ※ CustomerConsent の過去ログは絶対に上書きしない
    """
    user = request.user
    keep_uuid = request.data.get("keep_uuid")
    merged_uuid = request.data.get("merged_uuid")
    overwrite = bool(request.data.get("overwrite", False))

    # --- 1. バリデーション ---
    if not keep_uuid or not merged_uuid:
        return Response(
            {"error": "keep_uuid と merged_uuid は必須です"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if keep_uuid == merged_uuid:
        return Response(
            {"error": "同じ顧客同士はマージできません"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        keep_customer = Customer.objects.get(uuid=keep_uuid, user=user)
    except Customer.DoesNotExist:
        return Response(
            {"error": "keep_uuid の顧客が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        merged_customer = Customer.objects.get(uuid=merged_uuid, user=user)
    except Customer.DoesNotExist:
        return Response(
            {"error": "merged_uuid の顧客が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not keep_customer.is_active:
        return Response(
            {"error": "マージ先の顧客(keep)が無効化されています"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --- 2. マージ処理 ---
    with transaction.atomic():

        # 2-1) 顧客フィールドの統合（名前/電話等）
        merge_customer_fields(keep_customer, merged_customer, overwrite=overwrite)
        keep_customer.save()

        # 2-2) これまで merged_customer に統合されていた顧客も、
        #      まとめて keep_customer に付け替えてチェーンをフラット化
        #
        #   A -> B でマージ済みの状態で、
        #   さらに B -> C にマージするとき：
        #     - ここで A.merged_into も C に更新される
        #
        #   こうしておくと「何回マージしても最終アクティブ顧客」に
        #   たどり着くので、active_only フィルタで古い履歴が
        #   消える問題を防げる。
        Customer.objects.filter(merged_into=merged_customer).update(
            merged_into=keep_customer
        )

        # 2-3) merged_customer を「keep に統合された」状態にする
        merged_customer.is_active = False
        merged_customer.merged_into = keep_customer  # ← Customer モデルの FK
        merged_customer.save()

        # 2-4) マージログを記録
        CustomerMergeLog.objects.create(
            keep_uuid=keep_customer.uuid,
            merged_uuid=merged_customer.uuid,
            performed_by=user,
            overwrite=overwrite,
            details=f"顧客マージ: keep={keep_customer.uuid} ← merged={merged_customer.uuid}",
        )

    # --- 3. 返却 ---
    return Response(
        {
            "message": "顧客をマージしました",
            "keep_uuid": str(keep_customer.uuid),
            "merged_uuid": str(merged_customer.uuid),
        },
        status=status.HTTP_200_OK,
    )
