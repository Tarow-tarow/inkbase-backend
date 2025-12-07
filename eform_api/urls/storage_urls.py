# eform_api/urls/storage_urls.py
from django.urls import path
from eform_api.views.storage_views import (
    GeneratePresignedProfileImageUrlView,  # 既存ならそのまま
    UploadProfileImageView,                # 追加
)

urlpatterns = [
    path(
        "generate-presigned-profile-image-url/",
        GeneratePresignedProfileImageUrlView.as_view(),
        name="generate_presigned_profile_image_url",
    ),
    path(
        "upload-profile-image/",
        UploadProfileImageView.as_view(),
        name="upload_profile_image",
    ),
]
