# eform_api/urls/customer_urls.py

from django.urls import path
from ..views.customer_views import (
    CustomerListCreateAPIView,
    CustomerRetrieveUpdateAPIView,
    CustomerEasyCreateView,
    lookup_customer_by_phone,
    submit_customer_consent,
    merge_customers,  # ←★追加
)

urlpatterns = [
    path('', CustomerListCreateAPIView.as_view(),
         name='customer-list-create'),
    
    path('<uuid:uuid>/', CustomerRetrieveUpdateAPIView.as_view(),
         name='customer-detail'),

    path('easy-create/', CustomerEasyCreateView.as_view(),
         name='customer-easy-create'),

    path('lookup-by-phone/', lookup_customer_by_phone,
         name='lookup-customer-by-phone'),

    path('submit-consent/', submit_customer_consent,
         name='submit-customer-consent'),

    # ★ 顧客マージAPI（POST）
    path('merge/', merge_customers, name='customer-merge'),
]
