# eform_api/views/storage_views.py
import uuid

import boto3
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class GeneratePresignedProfileImageUrlView(APIView):
    """
    プロフィール画像アップロード用 プリサインドURL発行API

    フロントから:
      POST /api/storage/generate-presigned-profile-image-url/
      body: { "file_name": "avatar.png", "content_type": "image/png" }

    レスポンス:
      {
        "upload_url": "https://...s3...署名付きURL...",
        "file_url": "https://bucket.s3.ap-northeast-1.amazonaws.com/uploads/profile_image/xxxx.png",
        "object_key": "uploads/profile_image/xxxx.png"
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_name = request.data.get("file_name")
        content_type = request.data.get("content_type")

        if not file_name or not content_type:
            return Response(
                {"detail": "file_name と content_type は必須です。"},
                status=400,
            )

        if not content_type.startswith("image/"):
            return Response(
                {"detail": "画像ファイルのみアップロード可能です。"},
                status=400,
            )

        # 拡張子抽出
        ext = file_name.split(".")[-1].lower()
        # S3 上での保存パス（prefix 固定）
        object_key = f"uploads/profile_image/{uuid.uuid4()}.{ext}"

        # S3 クライアント
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        try:
            upload_url = s3.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": settings.AWS_S3_BUCKET_NAME,
                    "Key": object_key,
                    "ContentType": content_type,
                    # バケットポリシーで public-read を許可している前提なので ACL は省略
                    # 必要なら "ACL": "public-read" を追加
                },
                ExpiresIn=300,  # 5分
            )
        except Exception as e:
            return Response(
                {"detail": f"presigned URL の生成に失敗しました: {e}"},
                status=500,
            )

        file_url = f"{settings.AWS_S3_BASE_URL}/{object_key}"

        return Response(
            {
                "upload_url": upload_url,
                "file_url": file_url,
                "object_key": object_key,
            }
        )




class UploadProfileImageView(APIView):
    """
    プロフィール画像を Django 経由で S3 にアップロードするAPI
    フロントから multipart/form-data でファイルを送る。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get("file")

        if not file_obj:
            return Response({"detail": "file が送信されていません。"}, status=400)

        content_type = getattr(file_obj, "content_type", None) or ""
        if not content_type.startswith("image/"):
            return Response({"detail": "画像ファイルのみアップロード可能です。"}, status=400)

        # 拡張子をざっくり取得
        original_name = getattr(file_obj, "name", "upload")
        ext = original_name.split(".")[-1].lower() if "." in original_name else "jpg"

        # S3 上のパス
        object_key = f"uploads/profile_image/{uuid.uuid4()}.{ext}"

        # S3 クライアント
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        try:
            s3.upload_fileobj(
                Fileobj=file_obj,
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Key=object_key,
                ExtraArgs={"ContentType": content_type},
            )
        except Exception as e:
            return Response(
                {"detail": f"S3 へのアップロードに失敗しました: {e}"},
                status=500,
            )

        file_url = f"{settings.AWS_S3_BASE_URL}/{object_key}"

        return Response(
            {
                "file_url": file_url,
                "object_key": object_key,
            },
            status=201,
        )
