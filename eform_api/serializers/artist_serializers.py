from rest_framework import serializers
from ..models import TattooArtist

# ----------------------------------------
# 1(2).彫師モデル TattooArtist Serializer
# ----------------------------------------

class TattooArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = TattooArtist
        fields = '__all__'
        read_only_fields = ['uuid', 'user', 'created_at', 'updated_at']

        extra_kwargs = {
            # 🔽 ここに optional ルールを追加
            'real_name': {'required': False, 'allow_blank': True, 'allow_null': True},
            'gender': {'required': False, 'allow_blank': True, 'allow_null': True},
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'phone': {'required': False, 'allow_blank': True, 'allow_null': True},

            'artist_name': {'required': True},  # ← ここだけ必須でOK

            'studio_name': {'required': False, 'allow_blank': True, 'allow_null': True},
            'prefecture': {'required': False, 'allow_blank': True, 'allow_null': True},
            'specialties': {'required': False, 'allow_blank': True, 'allow_null': True},
            'bio': {'required': False, 'allow_blank': True, 'allow_null': True},

            'instagram_url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'line_url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'tiktok_url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'youtube_url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'x_url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'website_url': {'required': False, 'allow_blank': True, 'allow_null': True},

            'profile_image_url': {'required': False, 'allow_null': True},
        }
