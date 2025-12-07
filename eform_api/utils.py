import re
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from html import unescape


# ------------------------------
# 1. 電話番号正規化
# ------------------------------
def normalize_phone_number(phone: str) -> str:
    """
    電話番号を正規化する：
    - 全角 → 半角
    - ハイフン / 空白 / 括弧 / 記号 を削除
    - +81 や 81 で始まるものを 0 に変換
    - 英字や"TEL:"などのプレフィックスを削除
    """
    if not phone:
        return ''

    # 全角 → 半角変換（数字・記号）
    import unicodedata
    phone = unicodedata.normalize('NFKC', phone)

    # 英字プレフィックス削除（例: TEL:, Phone:）
    phone = re.sub(r'^[A-Za-z\s:]+', '', phone)

    # 記号・空白・括弧を除去
    phone = re.sub(r'[()\[\]\s\-–ー−―‐]', '', phone)

    # +81 や 81 で始まる番号を 0 に変換
    phone = re.sub(r'^\+?81', '0', phone)

    # 数字のみを残す（万が一の記号混入に備え）
    phone = re.sub(r'\D', '', phone)

    return phone

# ------------------------------
# 2. 本登録案内メールのtxt,html読み込み
# ------------------------------

def send_activation_email(user, activation_url):
    subject = "【INKBASE】仮登録のご案内"
    context = {
        "user": user,
        "activation_url": activation_url,
    }

    text_content = render_to_string("emails/activation_email.txt", context)
    html_content = render_to_string("emails/activation_email.html", context)

    msg = EmailMultiAlternatives(subject, text_content, to=[user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

# ------------------------------
# 3. パスワード再設定用メールのtxt,html読み込み
# ------------------------------
def send_reset_password_email(user, reset_url):
    subject = "【INKBASE】パスワード再設定のご案内"
    context = {
        'user': user,
        'reset_url': unescape(reset_url),  # ← ここで &amp; を & に戻す
    }
    text_content = render_to_string("emails/reset_password_email.txt", context)
    html_content = render_to_string("emails/reset_password_email.html", context)

    msg = EmailMultiAlternatives(subject, text_content, to=[user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
