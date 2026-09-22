from django.db import transaction
from django.utils import timezone

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
        if locked_order.payment_status != Order.PaymentStatus.PENDING:
            locked_order.payment_status = Order.PaymentStatus.PENDING
            locked_order.save(
                update_fields=(
                    "payment_status",
                    "updated_at",
                )
            )

        return existing_payment

    payment = Payment.objects.create(
        order=locked_order,
        method=method,
        provider=provider,
        status=Payment.Status.PENDING,
        amount=locked_order.total_amount,
    )

    if locked_order.payment_status != Order.PaymentStatus.PENDING:
        locked_order.payment_status = Order.PaymentStatus.PENDING
        locked_order.save(
            update_fields=(
                "payment_status",
                "updated_at",
            )
        )

    return payment


@transaction.atomic
def confirm_payment(
    *,
    payment,
    external_id,
):
    if external_id is None or not str(external_id).strip():
        raise PaymentError(
            "External payment ID is required."
        )

    external_id = str(external_id).strip()

    locked_payment = (
        Payment.objects
        .select_for_update()
        .get(pk=payment.pk)
    )

    locked_order = (
        Order.objects
        .select_for_update()
        .get(pk=locked_payment.order_id)
    )

    if locked_order.status == Order.Status.CANCELLED:
        raise PaymentError(
            "Cancelled orders cannot have payments confirmed."
        )

    if locked_payment.status in (
        Payment.Status.CANCELLED,
        Payment.Status.REFUNDED,
        Payment.Status.FAILED,
    ):
        raise PaymentError(
            f'Payment with status "{locked_payment.status}" '
            "cannot be confirmed."
        )

    duplicated_external_id = (
        Payment.objects
        .filter(
            provider=locked_payment.provider,
            external_id=external_id,
        )
        .exclude(pk=locked_payment.pk)
        .exists()
    )

    if duplicated_external_id:
        raise PaymentError(
            "External payment ID is already associated "
            "with another payment."
        )

    if (
        locked_payment.status == Payment.Status.PAID
        and locked_payment.external_id
        and locked_payment.external_id != external_id
    ):
        raise PaymentError(
            "Paid payment cannot change its external payment ID."
        )

    payment_fields = []

    if locked_payment.external_id != external_id:
        locked_payment.external_id = external_id
        payment_fields.append("external_id")

    if locked_payment.status != Payment.Status.PAID:
        locked_payment.status = Payment.Status.PAID
        payment_fields.append("status")

    if locked_payment.paid_at is None:
        locked_payment.paid_at = timezone.now()
        payment_fields.append("paid_at")

    if payment_fields:
        payment_fields.append("updated_at")
        locked_payment.save(
            update_fields=tuple(payment_fields)
        )

    order_fields = []

    if locked_order.payment_status != Order.PaymentStatus.PAID:
        locked_order.payment_status = Order.PaymentStatus.PAID
        order_fields.append("payment_status")

    if locked_order.status == Order.Status.PENDING:
        locked_order.status = Order.Status.CONFIRMED
        order_fields.append("status")

    if order_fields:
        order_fields.append("updated_at")
        locked_order.save(
            update_fields=tuple(order_fields)
        )

    return locked_payment


def _sync_order_after_unsuccessful_payment(order):
    if order.payments.filter(status=Payment.Status.PAID).exists():
        target_status = Order.PaymentStatus.PAID
    elif order.payments.filter(status=Payment.Status.PENDING).exists():
        target_status = Order.PaymentStatus.PENDING
    else:
        target_status = Order.PaymentStatus.FAILED

    if order.payment_status != target_status:
        order.payment_status = target_status
        order.save(
            update_fields=(
                "payment_status",
                "updated_at",
            )
        )


@transaction.atomic
def fail_payment(*, payment):
    locked_payment = (
        Payment.objects
        .select_for_update()
        .get(pk=payment.pk)
    )

    locked_order = (
        Order.objects
        .select_for_update()
        .get(pk=locked_payment.order_id)
    )

    if locked_payment.status == Payment.Status.FAILED:
        return locked_payment

    if locked_payment.status != Payment.Status.PENDING:
        raise PaymentError(
            f'Payment with status "{locked_payment.status}" '
            "cannot be marked as failed."
        )

    locked_payment.status = Payment.Status.FAILED
    locked_payment.save(
        update_fields=(
            "status",
            "updated_at",
        )
    )

    _sync_order_after_unsuccessful_payment(locked_order)

    return locked_payment


@transaction.atomic
def cancel_payment(*, payment):
    locked_payment = (
        Payment.objects
        .select_for_update()
        .get(pk=payment.pk)
    )

    locked_order = (
        Order.objects
        .select_for_update()
        .get(pk=locked_payment.order_id)
    )

    if locked_payment.status == Payment.Status.CANCELLED:
        return locked_payment

    if locked_payment.status != Payment.Status.PENDING:
        raise PaymentError(
            f'Payment with status "{locked_payment.status}" '
            "cannot be cancelled."
        )

    locked_payment.status = Payment.Status.CANCELLED
    locked_payment.save(
        update_fields=(
            "status",
            "updated_at",
        )
    )

    _sync_order_after_unsuccessful_payment(locked_order)

    return locked_payment


@transaction.atomic
def refund_payment(*, payment):
    locked_payment = (
        Payment.objects
        .select_for_update()
        .get(pk=payment.pk)
    )

    locked_order = (
        Order.objects
        .select_for_update()
        .get(pk=locked_payment.order_id)
    )

    if locked_payment.status == Payment.Status.REFUNDED:
        return locked_payment

    if locked_payment.status != Payment.Status.PAID:
        raise PaymentError(
            f'Payment with status "{locked_payment.status}" '
            "cannot be refunded."
        )

    locked_payment.status = Payment.Status.REFUNDED

    if locked_payment.refunded_at is None:
        locked_payment.refunded_at = timezone.now()

    locked_payment.save(
        update_fields=(
            "status",
            "refunded_at",
            "updated_at",
        )
    )

    locked_order.payment_status = Order.PaymentStatus.REFUNDED
    locked_order.save(
        update_fields=(
            "payment_status",
            "updated_at",
        )
    )

    return locked_payment
