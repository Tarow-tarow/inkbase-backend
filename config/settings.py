from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import os
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# ==========================
# 環境ごとの .env 切り替え
# ==========================
# DJANGO_ENV が "prod" なら .env.prod、
# それ以外（未設定や local）のときは .env.local を読む
ENV_NAME = os.getenv("DJANGO_ENV", "local")
env_file = BASE_DIR / f".env.{ENV_NAME}"

if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    # 念のためのフォールバック（開発で .env.local しかないケースなど）
    fallback = BASE_DIR / ".env.local"
    if fallback.exists():
        load_dotenv(dotenv_path=fallback)

# ====== 本番基本設定 ======
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "!!CHANGE_ME!!")  # ← 環境変数へ
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

# Amplify(現行) と 将来の独自ドメインを許可
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "54.95.246.35",
    "ec2-54-95-246-35.ap-northeast-1.compute.amazonaws.com",
    "api.inkbase.jp",
    "inkbase.jp",
    "www.inkbase.jp",
]

CSRF_TRUSTED_ORIGINS = [
    "http://54.95.246.35",
    "http://54.95.246.35:8000",
    "http://ec2-54-95-246-35.ap-northeast-1.compute.amazonaws.com",
    "https://inkbase.jp",
    "https://www.inkbase.jp",
    "https://api.inkbase.jp",
]
# ====== 諸々アプリ ======
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",    "rest_framework",
    "djoser",
    "corsheaders",
    "rest_framework.authtoken",
    "eform_api",
    "django_filters",
    "django_extensions",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "eform_api", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ====== DB（本番: RDS PostgreSQL）======
if ENV_NAME == "local":
    # ローカル環境 → SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # 本番など → RDS(PostgreSQL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

# ====== 認証 / REST ======
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

# ====== 国際化 ======
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# ====== Static / Media ======
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ====== CORS / CSRF ======
CORS_ALLOW_CREDENTIALS = True

# ★ ここを“明示リスト方式”に。CORS_ALLOW_ALL_ORIGINSは使わない
CORS_ALLOWED_ORIGINS = [
    "https://main.d2c780cwbqb4nq.amplifyapp.com",
    "https://inkbase.jp",
    "https://www.inkbase.jp",
    "http://localhost:3000",      # ローカル管理で必要なら残す
    "http://127.0.0.1:3000",
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
]

# ====== セキュアCookie / プロキシ ======
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False

CSRF_COOKIE_DOMAIN = "api.inkbase.jp"
SESSION_COOKIE_DOMAIN = "api.inkbase.jp"


# ====== メール（暫定: ファイル）======
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = BASE_DIR / "sent_emails"
DEFAULT_FROM_EMAIL = "noreply@inkbase.app"

# ====== フロントURL（通知等に使用）======
FRONTEND_URL = os.getenv(
    "FRONTEND_URL", "https://main.d2c780cwbqb4nq.amplifyapp.com")

# ====== MinIO / S3 ======
# いまはローカルの 192.168.* でクラウドから到達不可。早期にS3へ移行推奨。
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")  # 仮
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "uploads")
MINIO_REGION_NAME = os.getenv("MINIO_REGION_NAME", "ap-northeast-1")

# ====== S3 (Profile Images) ======
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "ap-northeast-1")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "inkbase-uploads")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

AWS_S3_BASE_URL = os.getenv(
    "AWS_S3_BASE_URL",
    f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com",
)
