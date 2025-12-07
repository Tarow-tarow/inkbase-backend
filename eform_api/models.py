# eform_api/models.py
from datetime import datetime
from django.db import models, transaction
from django.contrib.auth import get_user_model
import uuid
from .utils import normalize_phone_number

User = get_user_model()

# =========================
# Managers
# =========================

class ActiveManager(models.Manager):
    """Manager that returns only is_active=True records.
    # #manager #active-only
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


# =========================
# TattooArtist (彫師プロフィール)
# =========================

class TattooArtist(models.Model):
    """彫師プロフィール
    # #artist #profile #is_active
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    last_name = models.CharField(max_length=50, blank=True)
    first_name = models.CharField(max_length=50, blank=True)
    artist_name = models.CharField(max_length=100)
    furigana_name = models.CharField(max_length=100, blank=True)

    GENDER_CHOICES = [
        ('male', '男性'),
        ('female', '女性'),
        ('other', 'その他'),
        ('none', '無回答'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    birth_date = models.DateField(blank=True, null=True)

    studio_name = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    prefecture = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    google_maps_url = models.URLField(blank=True)

    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    instagram_url = models.URLField(blank=True)
    line_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    x_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    profile_image_url = models.URLField(max_length=500, blank=True, null=True)

    bio = models.TextField(blank=True)
    specialties = models.CharField(max_length=255, blank=True)

    is_public = models.BooleanField(default=True)
    accepting_clients = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)  # #is_active #soft-delete
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveManager()

    def __str__(self):
        return self.artist_name


# =========================
# Customer (顧客)
# =========================

class Customer(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')

    full_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name_kana = models.CharField(max_length=100, blank=True)
    first_name_kana = models.CharField(max_length=100, blank=True)

    GENDER_CHOICES = [
        ('male', '男性'),
        ('female', '女性'),
        ('other', 'その他'),
        ('none', '無回答'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    birth_date = models.CharField(max_length=10, blank=True, null=True)

    prefecture = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    instagram_id = models.CharField(max_length=100, blank=True)

    avatar_url = models.URLField(max_length=500, blank=True, null=True)

    notes = models.TextField(blank=True)

    skin_type = models.CharField(max_length=100, blank=True)
    tattoo_experience = models.BooleanField(default=False)
    occupation = models.CharField(max_length=100, blank=True)
    referrer = models.CharField(max_length=100, blank=True)
    mbti = models.CharField(max_length=4, blank=True)

    tattooist = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # soft delete
    is_active = models.BooleanField(default=True)

    # 🔽 追加：マージ先（参照されると過去 Consent は書き換え不要）
    merged_into = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="merged_from",
        help_text="この顧客が他の顧客にマージされた場合、その先"
    )

    objects = models.Manager()
    active = ActiveManager()

    def save(self, *args, **kwargs):
        if getattr(self, "phone_number", None):
            self.phone_number = normalize_phone_number(self.phone_number)
        super().save(*args, **kwargs)

# =========================
# CustomerConsent (同意履歴)
# =========================

class CustomerConsent(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE, related_name="consents")

    # 🔽 スナップショット（null/blank OK に変更）
    customer_uuid_snapshot = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
    )
    customer_name_snapshot = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        editable=False,
    )
    customer_birth_date_snapshot = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        editable=False,
    )
    customer_phone_snapshot = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        editable=False,
    )

    consent_version = models.CharField(max_length=20)
    signed_at = models.DateTimeField()
    signature = models.TextField(blank=True, null=True)
    privacy_agreement_version = models.CharField(max_length=20, blank=True)
    privacy_agreement_agreed_at = models.DateTimeField(blank=True, null=True)
    visit_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-signed_at']

    def save(self, *args, **kwargs):
        # 新規作成時だけスナップショットを埋める
        if self._state.adding and self.customer:
            # すでに手動でセットされていなければ上書き
            if self.customer_uuid_snapshot is None:
                self.customer_uuid_snapshot = self.customer.uuid
            if not self.customer_name_snapshot:
                self.customer_name_snapshot = self.customer.full_name or (
                    (self.customer.last_name or "") + (self.customer.first_name or "")
                ).strip()
            if not self.customer_birth_date_snapshot:
                self.customer_birth_date_snapshot = self.customer.birth_date or ""
            if not self.customer_phone_snapshot:
                self.customer_phone_snapshot = self.customer.phone_number or ""
        super().save(*args, **kwargs)

# =========================
# 監査ログ：CustomerMergeLog / CustomerDeleteLog
# =========================

class CustomerMergeLog(models.Model):
    """顧客統合（マージ）操作の監査ログ
    - keep_uuid: 統合先（残す側）
    - merged_uuid: 統合元（非アクティブ化される側）
    # #merge #audit
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    keep_uuid = models.UUIDField()   # 統合先顧客UUID
    merged_uuid = models.UUIDField() # 統合元顧客UUID
    performed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    performed_at = models.DateTimeField(auto_now_add=True)
    overwrite = models.BooleanField(default=False)  # 上書きポリシーだったか
    details = models.TextField(blank=True)          # 操作時の詳細（任意メモ）

    def __str__(self):
        return f"Merge {self.merged_uuid} -> {self.keep_uuid} by {self.performed_by}"


class CustomerDeleteLog(models.Model):
    """顧客削除（ソフトデリート）操作の監査ログ
    # #delete #audit
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    customer_uuid = models.UUIDField()
    performed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    performed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"Delete {self.customer_uuid} by {self.performed_by} at {self.performed_at}"


# =========================
# UserAgreement（そのまま）
# =========================

class UserAgreement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agreement')
    terms_version = models.CharField(max_length=50)
    terms_agreed_at = models.DateTimeField()
    privacy_version = models.CharField(max_length=50)
    privacy_agreed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Terms: {self.terms_version}, Privacy: {self.privacy_version}"

# =========================
# ConsentEntryToken（QR用トークン）
# =========================

class ConsentEntryToken(models.Model):
    """QRコード用の入場トークン
    - URLにはこの uuid だけを載せる
    - artist 単位で発行・無効化・期限管理ができる
    # #consent #entry-token
    """
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    artist = models.ForeignKey(
        "TattooArtist",
        on_delete=models.CASCADE,
        related_name="consent_entry_tokens",
    )

    # どの用途のトークンか（例: 店舗前POP / イベント用 など）
    label = models.CharField(max_length=100, blank=True)

    # 有効・無効フラグ
    is_active = models.BooleanField(default=True)

    # 有効期限（不要なら null のまま）
    expires_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(blank=True, null=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.artist.artist_name} token {self.uuid}"

    def is_valid(self) -> bool:
        """このトークンが現在有効かどうかを判定"""
        from django.utils import timezone

        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


# =========================
# ConsentAccessLog（アクセスログ）
# =========================

class ConsentAccessLog(models.Model):
    """公開同意フォームへのアクセスログ
    - 日次制限や不正利用検知に使う
    # #consent #access-log
    """
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    token = models.ForeignKey(
        "ConsentEntryToken",
        on_delete=models.CASCADE,
        related_name="access_logs",
    )

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    # 任意：電話番号での制限や分析に使う（無ければ空）
    customer_phone = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.token_id} @ {self.ip_address} ({self.created_at})"
