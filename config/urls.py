# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),                # 管理画面（/admin/）
    path('auth/', include('djoser.urls')),          # Djoser のAPI（/auth/）
    path('auth/', include('djoser.urls.jwt')),      # Djoser のJWT認証（/auth/jwt/）
    path('api/', include('eform_api.urls')),        # eform_api アプリのAPI（/api/...）
]

# MEDIAファイルの配信設定（DEBUG=True の時だけ）
# 本番環境ではS3などで処理されるため不要
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
