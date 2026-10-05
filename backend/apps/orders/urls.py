from django.urls import path

from .views import (
    CheckoutAPIView,
    MercadoPagoWebhookAPIView,
    OrderCancelAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    PaymentAttemptAPIView,
    PaymentCapabilitiesAPIView,
)


app_name = "orders"


urlpatterns = [
    path(
        "",
        OrderListAPIView.as_view(),
        name="list",
    ),
    path(
        "webhooks/mercado-pago/",
        MercadoPagoWebhookAPIView.as_view(),
        name="mercado-pago-webhook",
    ),
    path(
        "payment-capabilities/",
        PaymentCapabilitiesAPIView.as_view(),
        name="payment-capabilities",
    ),
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
        "<uuid:public_id>/cancel/",
        OrderCancelAPIView.as_view(),
        name="cancel",
    ),
    path(
        "<uuid:public_id>/payments/",
        PaymentAttemptAPIView.as_view(),
        name="payment-attempt",
    ),
]
