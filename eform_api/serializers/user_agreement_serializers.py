from rest_framework import serializers
from ..models import UserAgreement

# ----------------------------------------
# 1(7).ユーザー同意履歴 UserAgreementSerializer
# ----------------------------------------

class UserAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAgreement
        fields = '__all__'
        read_only_fields = ['user', 'created_at']