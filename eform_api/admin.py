from django.contrib import admin
from .models import Customer, TattooArtist, CustomerConsent, UserAgreement

# =========================================
# 顧客モデル（Customer）の管理画面設定
# =========================================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # 管理画面の一覧に表示するフィールド
    list_display = (
        'id',               # 顧客の内部ID
        'full_name',        # 表示名または氏名
        'user',             # 担当スタッフ（ForeignKeyで紐付いたDjangoユーザー）
        'gender',           # 性別
        'avatar_url',       # アバター画像
        'birth_date',       # 生年月日
        'created_at',       # 登録日時
        'is_active',
    )

    # サイドバーでのフィルター条件
    list_filter = (
        'gender',              # 性別で絞り込み
        'tattoo_experience',   # タトゥー経験の有無で絞り込み
        'created_at',          # 登録日で絞り込み
    )

    # 検索窓で対象とするフィールド
    search_fields = (
        'full_name',           # 表示名
        'last_name',           # 姓
        'first_name',          # 名
        'phone_number',        # 電話番号
        'instagram_id',        # Instagram ID
    )


# =========================================
# 彫師モデル（TattooArtist）の管理画面設定
# =========================================
@admin.register(TattooArtist)
class TattooArtistAdmin(admin.ModelAdmin):
    # 一覧表示されるフィールド
    list_display = (
        'artist_name',        # 彫師名（表示名）
        'profile_image_url',       # アバター画像
        'email',              # 連絡用メール
        'is_public',          # 公開フラグ（検索結果や一覧表示対象か）
        'accepting_clients',  # 新規受付中フラグ
        'created_at',         # 登録日時
        'is_active',
    )

    # 検索可能なフィールド
    search_fields = (
        'artist_name',        # 彫師名
        'email',              # メールアドレス
        'studio_name',        # スタジオ名
    )

    # フィルタリング可能なフィールド
    list_filter = (
        'is_public',          # 公開・非公開
        'accepting_clients',  # 新規受付の可否
        'prefecture',         # 都道府県ごとの絞り込み
    )


# =========================================
# 同意履歴モデル（CustomerConsent）の管理画面設定
# =========================================
@admin.register(CustomerConsent)
class CustomerConsentAdmin(admin.ModelAdmin):
    # 一覧に表示する項目
    list_display = (
        'customer',                # 紐付けられた顧客
        'consent_version',         # 同意書のバージョン
        'signed_at',               # 同意日時
        'privacy_agreement_version',  # プライバシーポリシーのバージョン
        'is_active',
    )

    # 検索対象フィールド（外部キーの中のフィールドも指定可能）
    search_fields = (
        'customer__full_name',       # 顧客の名前
        'consent_version',           # 同意書のバージョン
        'privacy_agreement_version',    # プライバシーポリシーのバージョン
    )

    # フィルターに使用する項目
    list_filter = (
        'consent_version',           # 同意書バージョンごとに絞り込み
        'privacy_agreement_version',    # プライバシーポリシーバージョンごとに絞り込み
    )

    # 誤編集を防ぐために読み取り専用にするフィールド
    readonly_fields = (
        'signed_at',                 # 同意日時は変更不可
        'created_at',                # DB作成日時
        'updated_at',                # 最終更新日時
    )

# =========================================
# User用の利用規約・プライバシーポリシー同意履歴モデル（UserAgreement）の管理画面設定
# =========================================
@admin.register(UserAgreement)
class UserAgreementAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'terms_version',
        'terms_agreed_at',
        'privacy_version',
        'privacy_agreed_at',
        'created_at',
    )
    list_filter = ('terms_version', 'privacy_version', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'terms_agreed_at', 'privacy_agreed_at', 'created_at')
    ordering = ('-created_at',)
