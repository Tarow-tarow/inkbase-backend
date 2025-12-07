from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from django.conf import settings

from ..models import  TattooArtist
from ..serializers import (
    RegisterSerializer,
)


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
import logging
from ..utils import send_reset_password_email

User = get_user_model()
logger = logging.getLogger(__name__)

# ------------------------------
# 1(1).会員登録時にTattooArtistも同時作成
# ------------------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []

    def perform_create(self, serializer):
        user = serializer.save()
        TattooArtist.objects.create(
            user=user,
            artist_name=user.username,
            email=user.email,
        )

# ------------------------------
# 2(9). 仮登録後のメール認証リンクから本登録に切り替えるAPI
# ------------------------------

class VerifyEmailView(APIView):
    def get(self, request):
        uidb64 = request.GET.get('uid')
        token = request.GET.get('token')

        if not uidb64 or not token:
            return Response({'detail': 'パラメータが不足しています'}, status=400)

        logger.info(f"📩 メール認証リクエスト uidb64={uidb64}, token={token}")

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            logger.warning(f"⚠️ ユーザーが見つかりませんでした（デコード失敗または存在しない）: uidb64={uidb64}")
            return Response({'detail': 'ユーザーが存在しません'}, status=status.HTTP_404_NOT_FOUND)

        if not default_token_generator.check_token(user, token):
            logger.warning(f"❌ トークン無効: uid={uid}, token={token}")
            return Response({'detail': 'トークンが無効または期限切れです'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        logger.info(f"✅ メール認証成功: uid={uid} → is_active=True")
        return Response({'detail': '本登録が完了しました'}, status=status.HTTP_200_OK)

# ------------------------------
# 3(10). パスワード再設定メールを送信するAPI
# ------------------------------

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email, is_active=True).first()

        if not user:
            return Response({"error": "登録されたメールアドレスが見つかりません。"}, status=status.HTTP_400_BAD_REQUEST)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?uid={uid}&token={token}"

        send_reset_password_email(user, reset_url)

        return Response({"message": "パスワード再設定用のメールを送信しました。"}, status=status.HTTP_200_OK)

# ------------------------------
# 4(11). パスワード再設定フォームから新パスワードを登録するAPI
# ------------------------------

class PasswordResetConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("password")

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(user, token):
                return Response({"error": "リンクが無効または期限切れです。"}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({"message": "パスワードを変更しました。"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("パスワードリセット失敗")
            return Response({"error": "無効なリクエストです。"}, status=status.HTTP_400_BAD_REQUEST)
