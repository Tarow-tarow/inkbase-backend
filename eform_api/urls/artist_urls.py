from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.artist_views import TattooArtistViewSet, ArtistStatsAPIView

router = DefaultRouter()
router.register(r'', TattooArtistViewSet, basename='tattoo-artist')

urlpatterns = [
    path('', include(router.urls)),
    path('<uuid:uuid>/stats/', ArtistStatsAPIView.as_view(), name='artist-stats'),
]
