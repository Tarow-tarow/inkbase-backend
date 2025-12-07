from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny

from ..models import TattooArtist, Customer, CustomerConsent
from ..serializers import (
    TattooArtistSerializer,
    ArtistStatsSerializer
)
from rest_framework.views import APIView
from django.db.models import Avg
from datetime import datetime
from django.shortcuts import get_object_or_404
from statistics import median


# ------------------------------
# 1(4).ログイン中の彫師プロフィール取得・編集（/artists/me）
# ------------------------------

class TattooArtistViewSet(viewsets.ModelViewSet):
    queryset = TattooArtist.objects.filter(is_public=True)
    serializer_class = TattooArtistSerializer
    permission_classes = [AllowAny]
    lookup_field = 'uuid'

    @action(
        detail=False,
        methods=['get', 'patch', 'post'],  # ← post を追加
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """ログイン中の彫師のプロフィール表示・編集・初回作成"""

        # まず、今のユーザーに紐づくプロフィールがあるか確認
        try:
            artist = TattooArtist.objects.get(user=request.user)
            exists = True
        except TattooArtist.DoesNotExist:
            artist = None
            exists = False

        # -------------------------
        # 1) プロフィール未登録のとき
        # -------------------------
        if not exists:
            # GET / PATCH のときは 404 を返す（フロントはこれを見て isNew=true にしている）
            if request.method in ['GET', 'PATCH']:
                return Response(
                    {'detail': 'プロフィール未登録'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # POST のときは「初回作成」として扱う
            if request.method == 'POST':
                serializer = self.get_serializer(
                    data=request.data,
                    context={'request': request},
                )
                if serializer.is_valid():
                    # user は body からではなく request.user で紐づける
                    serializer.save(user=request.user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # ここに来るのは「プロフィールが存在する」ケース

        # -------------------------
        # 2) 既にプロフィールがあるとき
        # -------------------------
        if request.method == 'GET':
            serializer = self.get_serializer(artist)
            return Response(serializer.data)

        if request.method == 'PATCH':
            serializer = self.get_serializer(
                artist,
                data=request.data,
                partial=True,
                context={'request': request},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            # 既にプロフィールがあるのに POST された場合
            return Response(
                {'detail': '既にプロフィールが存在します。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 想定外メソッド（ほぼ来ないはず）
        return Response(
            {'detail': 'Method not allowed.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

# ------------------------------
# 2. HOMEコンプリート後のカード 統計取得
# ------------------------------

class ArtistStatsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uuid):
        artist = get_object_or_404(TattooArtist, uuid=uuid)
        user = artist.user

        # この彫師に紐づく「現役顧客」
        customers = Customer.objects.filter(
            user=user,
            is_active=True,   # ★ 論理削除を除外（マージ済みも含めて）
        )

        # 顧客数（＝今生きている顧客だけ）
        customer_count = customers.count()

        # ✅ 同意書数：
        #  - この彫師(user)に紐づく CustomerConsent すべて
        #  - 顧客が is_active かどうかは見ない
        #  - 無効化された Consent だけ is_active で除外
        consent_count = CustomerConsent.objects.filter(
            customer__user=user,
            is_active=True,          # ← Consent 自体が有効なもの
        ).count()

        # 年齢計算（現役顧客だけを対象）
        ages = []
        for c in customers:
            if c.birth_date:
                try:
                    birth = datetime.strptime(c.birth_date, "%Y-%m-%d")
                    age = (datetime.now() - birth).days // 365
                    ages.append(age)
                except ValueError:
                    continue

        median_age = int(median(ages)) if ages else None

        return Response({
            "customer_count": customer_count,
            "consent_count": consent_count,
            "median_age": median_age,
            "username": artist.user.username,
        })
