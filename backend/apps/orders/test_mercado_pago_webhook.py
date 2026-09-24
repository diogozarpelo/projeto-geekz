from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Order, Payment, PaymentEvent
from .payment_services import (
    confirm_payment,
    create_payment_attempt,
)
from .providers.mercado_pago import MercadoPagoError


@override_settings(
    MERCADO_PAGO_WEBHOOK_SECRET="webhook-secret",
    MERCADO_PAGO_WEBHOOK_TOLERANCE_SECONDS=300,
)
class MercadoPagoWebhookTests(APITestCase):
    def setUp(self):
        self.order = Order.objects.create(
            customer_name="Cliente Webhook",
            customer_email="webhook@example.com",
            total_amount="149.90",
        )

        self.payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.PIX,
        )

        self.payment.provider_order_id = "ORD-WEBHOOK-001"
        self.payment.external_id = "PAY-WEBHOOK-001"
        self.payment.save(
            update_fields=(
                "provider_order_id",
                "external_id",
                "updated_at",
            )
        )

    def webhook_url(
        self,
        *,
        provider_order_id="ORD-WEBHOOK-001",
        notification_type="order",
    ):
        return (
            reverse("orders:mercado-pago-webhook")
            + f"?data.id={provider_order_id}"
            + f"&type={notification_type}"
        )

    def payload(
        self,
        *,
        notification_id="notification-001",
        action="order.updated",
    ):
        return {
            "id": notification_id,
            "action": action,
            "date_created": "2026-09-24T13:30:00Z",
            "data": {
                "id": self.payment.provider_order_id,
            },
        }

    def provider_order(
        self,
        *,
        status="action_required",
        status_detail="waiting_transfer",
        external_reference=None,
        provider_order_id="ORD-WEBHOOK-001",
        external_payment_id="PAY-WEBHOOK-001",
    ):
        if external_reference is None:
            external_reference = str(
                self.order.public_id
            )

        return {
            "id": provider_order_id,
            "external_reference": external_reference,
            "status": status,
            "status_detail": status_detail,
            "transactions": {
                "payments": [
                    {
                        "id": external_payment_id,
                        "status": status,
                        "status_detail": status_detail,
                    }
                ]
            },
        }

    def post_webhook(
        self,
        *,
        payload=None,
        provider_order_id="ORD-WEBHOOK-001",
        notification_type="order",
    ):
        return self.client.post(
            self.webhook_url(
                provider_order_id=provider_order_id,
                notification_type=notification_type,
            ),
            payload or self.payload(),
            format="json",
            HTTP_X_SIGNATURE="ts=123,v1=test-signature",
            HTTP_X_REQUEST_ID="request-001",
        )

    def test_invalid_signature_returns_unauthorized(self):
        response = self.client.post(
            self.webhook_url(),
            self.payload(),
            format="json",
            HTTP_X_REQUEST_ID="request-001",
        )

        self.assertEqual(
            response.status_code,
            401,
        )
        self.assertEqual(
            PaymentEvent.objects.count(),
            0,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_signature_validator_receives_expected_values(
        self,
        provider_class,
        validate_signature,
    ):
        provider_class.return_value.get_order.return_value = (
            self.provider_order()
        )

        response = self.post_webhook()

        self.assertEqual(
            response.status_code,
            200,
        )

        validate_signature.assert_called_once_with(
            "ts=123,v1=test-signature",
            "request-001",
            "ORD-WEBHOOK-001",
            "webhook-secret",
            tolerance_seconds=300,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_action_required_keeps_payment_pending(
        self,
        provider_class,
        validate_signature,
    ):
        provider_class.return_value.get_order.return_value = (
            self.provider_order(
                status="action_required",
                status_detail="waiting_transfer",
            )
        )

        response = self.post_webhook()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.PENDING,
        )
        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.PENDING,
        )
        self.assertEqual(
            PaymentEvent.objects.count(),
            1,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_processed_order_marks_payment_as_paid(
        self,
        provider_class,
        validate_signature,
    ):
        provider_class.return_value.get_order.return_value = (
            self.provider_order(
                status="processed",
                status_detail="accredited",
            )
        )

        response = self.post_webhook()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.PAID,
        )
        self.assertIsNotNone(
            self.payment.paid_at,
        )
        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.PAID,
        )
        self.assertEqual(
            self.order.status,
            Order.Status.CONFIRMED,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_failed_order_marks_payment_as_failed(
        self,
        provider_class,
        validate_signature,
    ):
        provider_class.return_value.get_order.return_value = (
            self.provider_order(
                status="failed",
                status_detail="failed",
            )
        )

        response = self.post_webhook()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.FAILED,
        )
        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.FAILED,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_canceled_order_marks_payment_as_cancelled(
        self,
        provider_class,
        validate_signature,
    ):
        provider_class.return_value.get_order.return_value = (
            self.provider_order(
                status="canceled",
                status_detail="canceled",
            )
        )

        response = self.post_webhook()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.CANCELLED,
        )
        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.FAILED,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_refunded_order_marks_payment_as_refunded(
        self,
        provider_class,
        validate_signature,
    ):
        confirm_payment(
            payment=self.payment,
            external_id=self.payment.external_id,
        )

        provider_class.return_value.get_order.return_value = (
            self.provider_order(
                status="refunded",
                status_detail="refunded",
            )
        )

        response = self.post_webhook()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.REFUNDED,
        )
        self.assertIsNotNone(
            self.payment.refunded_at,
        )
        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.REFUNDED,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_notification_is_idempotent(
        self,
        provider_class,
        validate_signature,
    ):
        provider_class.return_value.get_order.return_value = (
            self.provider_order(
                status="processed",
                status_detail="accredited",
            )
        )

        payload = self.payload(
            notification_id="notification-idempotent"
        )

        first_response = self.post_webhook(
            payload=payload,
        )
        second_response = self.post_webhook(
            payload=payload,
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )
        self.assertEqual(
            second_response.status_code,
            200,
        )

        self.assertEqual(
            PaymentEvent.objects.filter(
                provider=Payment.Provider.MERCADO_PAGO,
                event_id="notification-idempotent",
            ).count(),
            1,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.PAID,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_external_reference_mismatch_returns_conflict(
        self,
        provider_class,
        validate_signature,
    ):
        provider_class.return_value.get_order.return_value = (
            self.provider_order(
                external_reference="another-local-order",
            )
        )

        response = self.post_webhook()

        self.assertEqual(
            response.status_code,
            409,
        )
        self.assertEqual(
            PaymentEvent.objects.count(),
            0,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.PENDING,
        )

    @patch(
        "apps.orders.views.WebhookSignatureValidator.validate"
    )
    @patch(
        "apps.orders.views.MercadoPagoProvider"
    )
    def test_provider_failure_returns_bad_gateway(
        self,
        provider_class,
        validate_signature,
    ):
        provider_class.return_value.get_order.side_effect = (
            MercadoPagoError(
                "Could not retrieve Mercado Pago order."
            )
        )

        response = self.post_webhook()

        self.assertEqual(
            response.status_code,
            502,
        )
        self.assertEqual(
            PaymentEvent.objects.count(),
            0,
        )
