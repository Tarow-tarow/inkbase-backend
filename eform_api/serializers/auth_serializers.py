from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.safestring import mark_safe
from django.contrib.auth.tokens import default_token_generator

# ----------------------------
# 1.ユーザー登録用(仮登録) リンク踏ませるメール送信まで
# ----------------------------
User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="このメールアドレスは既に使用されています。")
        ]
    )
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="このユーザー名は既に使用されています。")
        ]
    )
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        

        verify_url = f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={token}"
        print("verify_url:", verify_url)

        context = {
        "user": user,
        "verify_url": mark_safe(verify_url),
        }

        text_content = render_to_string("emails/verify_email.txt", context)
        html_content = render_to_string("emails/verify_email.html", context)

        msg = EmailMultiAlternatives(
            subject="【INKBASE】メールアドレス認証のお願い",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return user


