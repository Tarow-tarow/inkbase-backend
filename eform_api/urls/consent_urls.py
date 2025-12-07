from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views.consent_views import CustomerConsentViewSet
from ..views.pdf_views import ConsentPdfView
from ..views.public_consent_views import (
    PublicConsentEntryView,
    PublicLookupCustomerByPhoneView,
    PublicConsentRenewView,
    PublicEntryTokenStatusView,
    PublicConsentEntryTokenCreateView,
)

router = DefaultRouter()
router.register(
    r'history',
    CustomerConsentViewSet,
    basename='customer-consent',
)

urlpatterns = [
    # /api/consent/history/...
    path('', include(router.urls)),

    # PDF
    path('pdf/<uuid:uuid>/', ConsentPdfView.as_view(), name='consent-pdf'),

    # 🔓 public 同意書 API
    path('public/entry/', PublicConsentEntryView.as_view(), name='public-consent-entry'),
    path('public/lookup-by-phone/', PublicLookupCustomerByPhoneView.as_view(), name='public-lookup-by-phone'),
    path('public/renew/', PublicConsentRenewView.as_view(), name='public-consent-renew'),
    path('public/token/<uuid:token_uuid>/', PublicEntryTokenStatusView.as_view(), name='public-consent-token-status'),

    # 新規トークン発行（認証必須）
    path('public/token/create/', PublicConsentEntryTokenCreateView.as_view(), name='public-consent-token-create'),
]
