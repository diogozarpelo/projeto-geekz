from django.urls import path

from .views import (
    CheckoutAPIView,
    OrderDetailAPIView,
    PaymentAttemptAPIView,
)


app_name = "orders"


urlpatterns = [
    path(
        "checkout/",
        CheckoutAPIView.as_view(),
        name="checkout",
    ),
    path(
        "<uuid:public_id>/",
        OrderDetailAPIView.as_view(),
        name="detail",
    ),
    path(
        "<uuid:public_id>/payments/",
        PaymentAttemptAPIView.as_view(),
        name="payment-attempt",
    ),
]
