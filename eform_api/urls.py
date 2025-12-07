# from django.urls import path, include
# from . import views
# from rest_framework.routers import DefaultRouter
# from rest_framework_simplejwt.views import (
#     TokenRefreshView, TokenVerifyView
# )
# from .views.token_views import CustomTokenObtainPairView
# from .views.user_views import (
#     RegisterView, VerifyEmailView, PasswordResetRequestView, PasswordResetConfirmView
# )
# from .views.artist_views import TattooArtistViewSet
# from .views.customer_views import CustomerViewSet, CustomerEasyCreateView, lookup_customer_by_phone
# from .views.consent_views import CustomerConsentViewSet
# from .views.agreement_views import UserAgreementCreateView, UserAgreementStatusView
# from .views.storage_views import GeneratePresignedUrlView
# from .views.artist_views import ArtistStatsAPIView
# from .views.pdf_views import ConsentPdfView
# from .views.public_consent_views import PublicConsentEntryView


# router = DefaultRouter()
# router.register(r'customers', CustomerViewSet, basename='customer')
# router.register(r'artists', TattooArtistViewSet, basename='tattoo-artist')
# router.register(r'customer-consents', CustomerConsentViewSet,
#                 basename='customer-consent')

# urlpatterns = [
#     # ヘルスチェック
#     path("health/", views.health, name="health"),

#     # 会員登録（彫師作成も同時）
#     path('register/', RegisterView.as_view(), name='register'),
#     # 会員登録仮登録後のメール
#     path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
#     # パスワード再設定用
#     path("request-password-reset/", PasswordResetRequestView.as_view(),
#          name="request-password-reset"),
#     path("reset-password/", PasswordResetConfirmView.as_view(),
#          name="reset-password"),

#     # Userの利用規約・プライバシーポリシー
#     path('policy-agree/', UserAgreementCreateView.as_view(), name='user-agreement'),
#     path("user-agreement/status/", UserAgreementStatusView.as_view(),
#          name='user-agreement-status'),

#     # JWT認証
#     path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

#     # PDF生成用
#     path('consent/pdf/<uuid:uuid>/', ConsentPdfView.as_view(), name='consent-pdf'),

#     # Home統計取得用
#     path('artists/<uuid:uuid>/stats/',
#          ArtistStatsAPIView.as_view(), name='artist-stats'),

#     # 顧客簡易追加
#     path('customers/easy-create/', CustomerEasyCreateView.as_view(),
#          name='customer-easy-create'),

#     # 電話番号顧客検索
#     path('customers/lookup-by-phone/', lookup_customer_by_phone,
#          name='lookup-customer-by-phone'),

#     # MinIO
#     path('generate-presigned-url/', GeneratePresignedUrlView.as_view(),
#          name='generate_presigned_url'),

#     # ViewSetルーティング
#     path('', include(router.urls)),

#     # public同意書用 API を追加
#     path('public/consent/entry/', PublicConsentEntryView.as_view(), name='public-consent-entry'),
# ]
