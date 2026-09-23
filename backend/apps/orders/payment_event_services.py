from django.db import transaction
from django.utils import timezone

from .models import Payment, PaymentEvent
from .payment_services import (
    PaymentError,
    cancel_payment,
    confirm_payment,
    fail_payment,
    refund_payment,
)


class PaymentEventError(ValueError):
    pass


NORMALIZED_PAYMENT_STATUSES = {
    "pending",
    "paid",
    "failed",
    "cancelled",
    "refunded",
}


def _normalize_text(value):
    if value is None:
        return ""

    return str(value).strip()


def _validate_provider(provider):
    valid_providers = {
        choice_value
        for choice_value, _ in Payment.Provider.choices
    }

    if provider not in valid_providers:
        raise PaymentEventError(
            f"Invalid payment provider: {provider}."
        )

    return provider


def _resolve_payment(
    *,
    payment,
    provider,
    external_payment_id,
):
    if payment is not None:
        try:
            return Payment.objects.get(pk=payment.pk)
        except Payment.DoesNotExist as exc:
            raise PaymentEventError(
                "Payment could not be resolved."
            ) from exc

    if external_payment_id:
        resolved_payment = (
            Payment.objects
            .filter(
                provider=provider,
                external_id=external_payment_id,
            )
            .first()
        )

        if resolved_payment is not None:
            return resolved_payment

    raise PaymentEventError(
        "Payment could not be resolved."
    )


def _apply_normalized_status(
    *,
    payment,
    status,
    external_payment_id,
):
    if status == "pending":
        return payment

    if status == "paid":
        return confirm_payment(
            payment=payment,
            external_id=external_payment_id,
        )

    if status == "failed":
        return fail_payment(
            payment=payment,
        )

    if status == "cancelled":
        return cancel_payment(
            payment=payment,
        )

    if status == "refunded":
        return refund_payment(
            payment=payment,
        )

    raise PaymentEventError(
        f"Unsupported normalized payment status: {status}."
    )


def process_normalized_payment_event(
    *,
    external_status,
    payment=None,
    provider=Payment.Provider.MERCADO_PAGO,
    event_id="",
    event_type="",
    external_payment_id="",
    payload=None,
):
    provider = _validate_provider(provider)

    external_status = _normalize_text(
        external_status
    ).lower()
    event_id = _normalize_text(event_id)
    event_type = _normalize_text(event_type)
    external_payment_id = _normalize_text(
        external_payment_id
    )

    if not external_status:
        raise PaymentEventError(
            "External payment status is required."
        )

    if external_status not in NORMALIZED_PAYMENT_STATUSES:
        raise PaymentEventError(
            "Unsupported normalized payment status: "
            f"{external_status}."
        )

    if payload is None:
        payload = {}

    if not isinstance(payload, dict):
        raise PaymentEventError(
            "Payment event payload must be a dictionary."
        )

    caught_error = None
    processed_event = None

    with transaction.atomic():
        existing_event = None

        if event_id:
            existing_event = (
                PaymentEvent.objects
                .select_for_update()
                .filter(
                    provider=provider,
                    event_id=event_id,
                )
                .first()
            )

        if (
            existing_event is not None
            and existing_event.processed_at is not None
        ):
            return existing_event

        if existing_event is None:
            processed_event = PaymentEvent.objects.create(
                payment=payment,
                provider=provider,
                event_id=event_id,
                event_type=event_type,
                external_payment_id=external_payment_id,
                external_status=external_status,
                payload=payload,
            )
        else:
            processed_event = existing_event

            changed_fields = []

            if (
                processed_event.payment_id is None
                and payment is not None
            ):
                processed_event.payment = payment
                changed_fields.append("payment")

            if changed_fields:
                processed_event.save(
                    update_fields=tuple(changed_fields)
                )

        try:
            resolved_payment = _resolve_payment(
                payment=payment or processed_event.payment,
                provider=provider,
                external_payment_id=external_payment_id,
            )

            if processed_event.payment_id != resolved_payment.pk:
                processed_event.payment = resolved_payment
                processed_event.save(
                    update_fields=("payment",)
                )

            _apply_normalized_status(
                payment=resolved_payment,
                status=external_status,
                external_payment_id=external_payment_id,
            )

        except (PaymentError, PaymentEventError) as exc:
            processed_event.processing_error = str(exc)
            processed_event.save(
                update_fields=("processing_error",)
            )
            caught_error = PaymentEventError(str(exc))

        else:
            processed_event.processed_at = timezone.now()
            processed_event.processing_error = ""
            processed_event.save(
                update_fields=(
                    "processed_at",
                    "processing_error",
                )
            )

    if caught_error is not None:
        raise caught_error

    return processed_event
