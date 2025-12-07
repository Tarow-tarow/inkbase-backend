from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from ..views.token_views import CustomTokenObtainPairView
from ..views.user_views import PasswordResetRequestView, PasswordResetConfirmView
from ..views.user_views import VerifyEmailView

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("request-password-reset/", PasswordResetRequestView.as_view(),
         name="request-password-reset"),
    path("reset-password/", PasswordResetConfirmView.as_view(),
         name="reset-password"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
]
