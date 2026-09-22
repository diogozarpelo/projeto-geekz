from django.db import transaction

from .models import Order, Payment


class PaymentError(ValueError):
    pass


def _validate_choice(value, choices, field_name):
    valid_values = {choice_value for choice_value, _ in choices}

    if value not in valid_values:
        raise PaymentError(
            f"Invalid {field_name}: {value}."
        )

    return value


@transaction.atomic
def create_payment_attempt(
    *,
    order,
    method,
    provider=Payment.Provider.MERCADO_PAGO,
):
    method = _validate_choice(
        method,
        Payment.Method.choices,
        "payment method",
    )
    provider = _validate_choice(
        provider,
        Payment.Provider.choices,
        "payment provider",
    )

    locked_order = (
        Order.objects
        .select_for_update()
        .get(pk=order.pk)
    )

    if locked_order.status == Order.Status.CANCELLED:
        raise PaymentError(
            "Cancelled orders cannot receive payments."
        )

    if locked_order.payment_status == Order.PaymentStatus.PAID:
        raise PaymentError(
            "This order is already paid."
        )

    if locked_order.total_amount <= 0:
        raise PaymentError(
            "Orders with zero total do not require payment."
        )

    existing_payment = (
        Payment.objects
        .filter(
            order=locked_order,
            method=method,
            provider=provider,
            status=Payment.Status.PENDING,
        )
        .order_by("-created_at")
        .first()
    )

    if existing_payment:
        return existing_payment

    return Payment.objects.create(
        order=locked_order,
        method=method,
        provider=provider,
        status=Payment.Status.PENDING,
        amount=locked_order.total_amount,
    )
