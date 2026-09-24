from decimal import Decimal

from django.test import TestCase, override_settings

from .models import Order, Payment
from .payment_services import create_payment_attempt
from .providers.mercado_pago import (
    MercadoPagoError,
    MercadoPagoProvider,
)


class FakeOrderResource:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, payload, request_options):
        self.calls.append(
            {
                "payload": payload,
                "headers": dict(
                    request_options.custom_headers
                ),
            }
        )

        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


class FakeSDK:
    def __init__(self, responses):
        self.order_resource = FakeOrderResource(
            responses
        )

    def order(self):
        return self.order_resource


def successful_pix_response(
    *,
    order_id="ORD-TEST-001",
    payment_id="PAY-TEST-001",
):
    return {
        "status": 201,
        "response": {
            "id": order_id,
            "status": "action_required",
            "status_detail": "waiting_transfer",
            "transactions": {
                "payments": [
                    {
                        "id": payment_id,
                        "status": "action_required",
                        "status_detail": "waiting_transfer",
                        "payment_method": {
                            "ticket_url": (
                                "https://mercadopago.example/pix"
                            ),
                            "qr_code": (
                                "000201010212TESTPIX"
                            ),
                            "qr_code_base64": (
                                "BASE64-PIX-IMAGE"
                            ),
                        },
                    }
                ]
            },
        },
    }


class MercadoPagoProviderTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            customer_name="Cliente Mercado Pago",
            customer_email="mp@example.com",
            total_amount=Decimal("149.90"),
        )

        self.payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.PIX,
        )

    @override_settings(
        MERCADO_PAGO_ACCESS_TOKEN=""
    )
    def test_access_token_is_required_without_injected_sdk(self):
        with self.assertRaisesMessage(
            MercadoPagoError,
            "Mercado Pago access token is not configured.",
        ):
            MercadoPagoProvider()

    def test_create_pix_order_persists_provider_data(self):
        sdk = FakeSDK(
            [
                successful_pix_response(),
            ]
        )

        provider = MercadoPagoProvider(
            sdk=sdk,
        )

        payment = provider.create_pix_order(
            payment=self.payment,
        )

        payment.refresh_from_db()

        self.assertEqual(
            payment.provider_order_id,
            "ORD-TEST-001",
        )
        self.assertEqual(
            payment.external_id,
            "PAY-TEST-001",
        )
        self.assertTrue(
            payment.idempotency_key,
        )
        self.assertEqual(
            payment.provider_data["order_status"],
            "action_required",
        )
        self.assertEqual(
            payment.provider_data[
                "order_status_detail"
            ],
            "waiting_transfer",
        )
        self.assertEqual(
            payment.provider_data["qr_code"],
            "000201010212TESTPIX",
        )
        self.assertEqual(
            payment.provider_data[
                "qr_code_base64"
            ],
            "BASE64-PIX-IMAGE",
        )
        self.assertEqual(
            payment.provider_data["ticket_url"],
            "https://mercadopago.example/pix",
        )

    def test_pix_payload_and_idempotency_header_are_sent(self):
        sdk = FakeSDK(
            [
                successful_pix_response(),
            ]
        )

        provider = MercadoPagoProvider(
            sdk=sdk,
        )

        provider.create_pix_order(
            payment=self.payment,
        )

        self.payment.refresh_from_db()

        call = sdk.order_resource.calls[0]
        payload = call["payload"]
        headers = call["headers"]

        self.assertEqual(
            payload["type"],
            "online",
        )
        self.assertEqual(
            payload["processing_mode"],
            "automatic",
        )
        self.assertEqual(
            payload["total_amount"],
            "149.90",
        )
        self.assertEqual(
            payload["external_reference"],
            str(self.order.public_id),
        )
        self.assertEqual(
            payload["payer"]["email"],
            "mp@example.com",
        )

        provider_payment = (
            payload["transactions"]["payments"][0]
        )

        self.assertEqual(
            provider_payment["amount"],
            "149.90",
        )
        self.assertEqual(
            provider_payment["payment_method"]["id"],
            "pix",
        )
        self.assertEqual(
            provider_payment["payment_method"]["type"],
            "bank_transfer",
        )
        self.assertEqual(
            headers["x-idempotency-key"],
            self.payment.idempotency_key,
        )

    def test_existing_provider_order_is_not_created_twice(self):
        sdk = FakeSDK(
            [
                successful_pix_response(),
            ]
        )

        provider = MercadoPagoProvider(
            sdk=sdk,
        )

        first_payment = provider.create_pix_order(
            payment=self.payment,
        )

        second_payment = provider.create_pix_order(
            payment=first_payment,
        )

        self.assertEqual(
            first_payment.pk,
            second_payment.pk,
        )
        self.assertEqual(
            len(sdk.order_resource.calls),
            1,
        )

    def test_idempotency_key_is_reused_after_provider_failure(self):
        sdk = FakeSDK(
            [
                {
                    "status": 500,
                    "response": {
                        "message": "temporary error",
                    },
                },
                successful_pix_response(
                    order_id="ORD-RETRY-001",
                    payment_id="PAY-RETRY-001",
                ),
            ]
        )

        provider = MercadoPagoProvider(
            sdk=sdk,
        )

        with self.assertRaisesMessage(
            MercadoPagoError,
            "temporary error",
        ):
            provider.create_pix_order(
                payment=self.payment,
            )

        self.payment.refresh_from_db()

        first_key = self.payment.idempotency_key

        self.assertTrue(first_key)
        self.assertEqual(
            self.payment.provider_order_id,
            "",
        )
        self.assertEqual(
            self.payment.external_id,
            "",
        )

        provider.create_pix_order(
            payment=self.payment,
        )

        self.payment.refresh_from_db()

        second_key = self.payment.idempotency_key

        self.assertEqual(
            first_key,
            second_key,
        )
        self.assertEqual(
            len(sdk.order_resource.calls),
            2,
        )
        self.assertEqual(
            sdk.order_resource.calls[0][
                "headers"
            ]["x-idempotency-key"],
            sdk.order_resource.calls[1][
                "headers"
            ]["x-idempotency-key"],
        )
        self.assertEqual(
            self.payment.provider_order_id,
            "ORD-RETRY-001",
        )

    def test_credit_card_payment_cannot_create_pix_order(self):
        card_payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.CREDIT_CARD,
        )

        sdk = FakeSDK(
            [
                successful_pix_response(),
            ]
        )

        provider = MercadoPagoProvider(
            sdk=sdk,
        )

        with self.assertRaisesMessage(
            MercadoPagoError,
            "Payment method is not Pix.",
        ):
            provider.create_pix_order(
                payment=card_payment,
            )

        self.assertEqual(
            len(sdk.order_resource.calls),
            0,
        )

    def test_incomplete_provider_identifiers_are_rejected(self):
        self.payment.provider_order_id = (
            "ORD-INCOMPLETE"
        )
        self.payment.save(
            update_fields=(
                "provider_order_id",
                "updated_at",
            )
        )

        sdk = FakeSDK(
            [
                successful_pix_response(),
            ]
        )

        provider = MercadoPagoProvider(
            sdk=sdk,
        )

        with self.assertRaisesMessage(
            MercadoPagoError,
            "Payment has incomplete Mercado Pago identifiers.",
        ):
            provider.create_pix_order(
                payment=self.payment,
            )

        self.assertEqual(
            len(sdk.order_resource.calls),
            0,
        )
