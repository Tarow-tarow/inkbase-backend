from django.urls import path
from ..views.user_views import RegisterView
from ..views.agreement_views import UserAgreementCreateView, UserAgreementStatusView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('policy-agree/', UserAgreementCreateView.as_view(), name='user-agreement'),
    path('agreement-status/', UserAgreementStatusView.as_view(),
         name='user-agreement-status'),
]
