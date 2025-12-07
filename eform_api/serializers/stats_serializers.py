from rest_framework import serializers

# ----------------------------------------
# 1(8). HOMEコンプリート後のカード
# ----------------------------------------

class ArtistStatsSerializer(serializers.Serializer):
    artist_name = serializers.CharField()
    username = serializers.CharField()
    profile_image_url = serializers.URLField(allow_null=True)
    customer_count = serializers.IntegerField()
    consent_count = serializers.IntegerField()
    median_age = serializers.IntegerField(allow_null=True) 
