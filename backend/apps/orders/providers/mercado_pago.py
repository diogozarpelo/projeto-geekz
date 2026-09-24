import uuid
from decimal import Decimal

import mercadopago
from django.conf import settings
from django.db import transaction

from ..models import Payment


class MercadoPagoError(ValueError):
    pass


def _format_amount(value):
    amount = Decimal(value)

    return format(
        amount.quantize(Decimal("0.01")),
        ".2f",
    )


def _first_payment(response):
    transactions = response.get("transactions") or {}
    payments = transactions.get("payments") or []

    if not payments:
        raise MercadoPagoError(
            "Mercado Pago response does not contain a payment transaction."
        )

    payment = payments[0]

    if not isinstance(payment, dict):
        raise MercadoPagoError(
            "Mercado Pago returned an invalid payment transaction."
        )

    return payment


def normalize_order_status(
    status,
    status_detail="",
):
    status = str(status or "").strip().lower()
    status_detail = str(
        status_detail or ""
    ).strip().lower()

    if status in {
        "created",
        "processing",
        "action_required",
    }:
        return "pending"

    if status == "processed":
        return "paid"

    if status == "failed":
        return "failed"

    if status in {
        "canceled",
        "cancelled",
        "expired",
    }:
        return "cancelled"

    if status == "refunded":
        return "refunded"

    if status == "charged_back":
        if status_detail == "reimbursed":
            return "refunded"

        if status_detail in {
            "in_process",
            "settled",
        }:
            return "paid"

    raise MercadoPagoError(
        "Unsupported Mercado Pago order status: "
        f"{status or '<empty>'}"
        + (
            f" / {status_detail}"
            if status_detail
            else ""
        )
        + "."
    )


class MercadoPagoProvider:
    def __init__(
        self,
        *,
        access_token=None,
        sdk=None,
    ):
        self.access_token = (
            access_token
            if access_token is not None
            else settings.MERCADO_PAGO_ACCESS_TOKEN
        )

        if sdk is not None:
            self.sdk = sdk
            return

        if not self.access_token:
            raise MercadoPagoError(
                "Mercado Pago access token is not configured."
            )

        self.sdk = mercadopago.SDK(
            self.access_token
        )

    def _ensure_idempotency_key(self, payment):
        with transaction.atomic():
            locked_payment = (
                Payment.objects
                .select_for_update()
                .get(pk=payment.pk)
            )

            if not locked_payment.idempotency_key:
                locked_payment.idempotency_key = str(
                    uuid.uuid4()
                )
                locked_payment.save(
                    update_fields=(
                        "idempotency_key",
                        "updated_at",
                    )
                )

            return locked_payment.idempotency_key

    def _build_pix_order_payload(self, payment):
        order = payment.order
        amount = _format_amount(
            payment.amount
        )

        return {
            "type": "online",
            "processing_mode": "automatic",
            "total_amount": amount,
            "external_reference": str(
                order.public_id
            ),
            "transactions": {
                "payments": [
                    {
                        "amount": amount,
                        "payment_method": {
                            "id": "pix",
                            "type": "bank_transfer",
                        },
                    }
                ]
            },
            "payer": {
                "email": order.customer_email,
            },
        }

    def get_order(self, *, provider_order_id):
        provider_order_id = str(
            provider_order_id or ""
        ).strip()

        if not provider_order_id:
            raise MercadoPagoError(
                "Mercado Pago order ID is required."
            )

        try:
            result = self.sdk.order().get(
                provider_order_id
            )
        except Exception as exc:
            raise MercadoPagoError(
                "Could not retrieve Mercado Pago order."
            ) from exc

        if not isinstance(result, dict):
            raise MercadoPagoError(
                "Mercado Pago returned an invalid response."
            )

        http_status = result.get("status")
        response = result.get("response")

        if (
            not isinstance(http_status, int)
            or http_status < 200
            or http_status >= 300
            or not isinstance(response, dict)
        ):
            message = (
                response.get("message")
                if isinstance(response, dict)
                else None
            )

            raise MercadoPagoError(
                message
                or "Mercado Pago rejected the order query."
            )

        response_order_id = str(
            response.get("id") or ""
        ).strip()

        if response_order_id != provider_order_id:
            raise MercadoPagoError(
                "Mercado Pago returned an unexpected order ID."
            )

        return response

    def create_pix_order(self, *, payment):
        payment = (
            Payment.objects
            .select_related("order")
            .get(pk=payment.pk)
        )

        if (
            payment.provider
            != Payment.Provider.MERCADO_PAGO
        ):
            raise MercadoPagoError(
                "Payment provider is not Mercado Pago."
            )

        if payment.method != Payment.Method.PIX:
            raise MercadoPagoError(
                "Payment method is not Pix."
            )

        if payment.status != Payment.Status.PENDING:
            raise MercadoPagoError(
                "Only pending payments can create a Pix order."
            )

        if (
            payment.provider_order_id
            and payment.external_id
        ):
            return payment

        if (
            payment.provider_order_id
            or payment.external_id
        ):
            raise MercadoPagoError(
                "Payment has incomplete Mercado Pago identifiers."
            )

        idempotency_key = (
            self._ensure_idempotency_key(
                payment
            )
        )

        payload = self._build_pix_order_payload(
            payment
        )

        request_options = (
            mercadopago.config.RequestOptions()
        )
        request_options.custom_headers = {
            "x-idempotency-key": idempotency_key,
        }

        try:
            result = self.sdk.order().create(
                payload,
                request_options,
            )
        except Exception as exc:
            raise MercadoPagoError(
                "Could not create Mercado Pago Pix order."
            ) from exc

        if not isinstance(result, dict):
            raise MercadoPagoError(
                "Mercado Pago returned an invalid response."
            )

        http_status = result.get("status")
        response = result.get("response")

        if (
            not isinstance(http_status, int)
            or http_status < 200
            or http_status >= 300
            or not isinstance(response, dict)
        ):
            message = (
                response.get("message")
                if isinstance(response, dict)
                else None
            )

            raise MercadoPagoError(
                message
                or "Mercado Pago rejected the Pix order."
            )

        provider_order_id = str(
            response.get("id") or ""
        ).strip()

        provider_payment = _first_payment(
            response
        )

        external_id = str(
            provider_payment.get("id") or ""
        ).strip()

        if not provider_order_id:
            raise MercadoPagoError(
                "Mercado Pago response does not contain an order ID."
            )

        if not external_id:
            raise MercadoPagoError(
                "Mercado Pago response does not contain a payment ID."
            )

        payment_method = (
            provider_payment.get(
                "payment_method"
            )
            or {}
        )

        public_provider_data = {
            "order_status": response.get(
                "status",
                "",
            ),
            "order_status_detail": response.get(
                "status_detail",
                "",
            ),
            "payment_status": provider_payment.get(
                "status",
                "",
            ),
            "payment_status_detail": provider_payment.get(
                "status_detail",
                "",
            ),
            "ticket_url": payment_method.get(
                "ticket_url",
                "",
            ),
            "qr_code": payment_method.get(
                "qr_code",
                "",
            ),
            "qr_code_base64": payment_method.get(
                "qr_code_base64",
                "",
            ),
        }

        with transaction.atomic():
            locked_payment = (
                Payment.objects
                .select_for_update()
                .get(pk=payment.pk)
            )

            if (
                locked_payment.provider_order_id
                and (
                    locked_payment.provider_order_id
                    != provider_order_id
                )
            ):
                raise MercadoPagoError(
                    "Payment is already associated with another "
                    "Mercado Pago order."
                )

            if (
                locked_payment.external_id
                and (
                    locked_payment.external_id
                    != external_id
                )
            ):
                raise MercadoPagoError(
                    "Payment is already associated with another "
                    "Mercado Pago payment."
                )

            locked_payment.provider_order_id = (
                provider_order_id
            )
            locked_payment.external_id = external_id
            locked_payment.provider_data = (
                public_provider_data
            )

            locked_payment.save(
                update_fields=(
                    "provider_order_id",
                    "external_id",
                    "provider_data",
                    "updated_at",
                )
            )

        return locked_payment
