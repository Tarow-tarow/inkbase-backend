# eform_api/urls/__init__.py
from django.urls import path, include
from eform_api.views.health import health

urlpatterns = [
    path("health/", health, name="health"),

    # 認証・ユーザー
    path('auth/', include('eform_api.urls.auth_urls')),
    path('user/', include('eform_api.urls.user_urls')),

    # メイン機能
    path('artists/', include('eform_api.urls.artist_urls')),
    path('customers/', include('eform_api.urls.customer_urls')),
    path('consent/', include('eform_api.urls.consent_urls')),
    path('storage/', include('eform_api.urls.storage_urls')),
]
