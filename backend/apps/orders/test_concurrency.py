from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.db import IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase

from .models import Order, Payment, PaymentEvent
from .payment_event_services import process_normalized_payment_event
from .payment_services import (
    PaymentError,
    confirm_payment,
    create_payment_attempt,
    refund_payment,
)


class PaymentConsistencyTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            customer_name="Cliente Consistencia",
            customer_email="consistency@example.com",
            total_amount=Decimal("129.90"),
        )

        self.pix_payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.PIX,
        )

    def test_second_payment_cannot_be_confirmed_after_order_is_paid(self):
        card_payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.CREDIT_CARD,
        )

        confirm_payment(
            payment=self.pix_payment,
            external_id="PAY-FIRST-001",
        )

        with self.assertRaisesMessage(
            PaymentError,
            "This order already has another paid payment.",
        ):
            confirm_payment(
                payment=card_payment,
                external_id="PAY-SECOND-001",
            )

        card_payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(
            card_payment.status,
            Payment.Status.PENDING,
        )
        self.assertEqual(
            card_payment.external_id,
            "",
        )
        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.PAID,
        )

    def test_refunded_order_cannot_receive_new_payment(self):
        confirm_payment(
            payment=self.pix_payment,
            external_id="PAY-REFUNDED-001",
        )

        refund_payment(
            payment=self.pix_payment,
        )

        self.order.refresh_from_db()

        with self.assertRaisesMessage(
            PaymentError,
            "Refunded orders cannot receive new payments.",
        ):
            create_payment_attempt(
                order=self.order,
                method=Payment.Method.PIX,
            )

    def test_database_rejects_second_paid_payment(self):
        confirm_payment(
            payment=self.pix_payment,
            external_id="PAY-DB-FIRST-001",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    order=self.order,
                    method=Payment.Method.CREDIT_CARD,
                    provider=Payment.Provider.MERCADO_PAGO,
                    status=Payment.Status.PAID,
                    amount=self.order.total_amount,
                    external_id="PAY-DB-SECOND-001",
                )


class PaymentEventConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.order = Order.objects.create(
            customer_name="Cliente Evento Concorrente",
            customer_email="event-concurrency@example.com",
            total_amount=Decimal("149.90"),
        )

        self.payment = create_payment_attempt(
            order=self.order,
            method=Payment.Method.PIX,
        )

    def _process_event(self, barrier):
        connection.close()

        try:
            payment = Payment.objects.get(
                pk=self.payment.pk,
            )

            barrier.wait(timeout=10)

            event = process_normalized_payment_event(
                payment=payment,
                external_status="pending",
                event_id="EVENT-CONCURRENT-001",
                event_type="payment.updated",
                external_payment_id="PAY-CONCURRENT-001",
                payload={
                    "source": "concurrency-test",
                },
            )

            return event.pk
        finally:
            connection.close()

    def test_duplicate_concurrent_event_is_processed_once(self):
        barrier = Barrier(2)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    self._process_event,
                    barrier,
                )
                for _ in range(2)
            ]

            event_ids = [
                future.result(timeout=15)
                for future in futures
            ]

        self.assertEqual(
            event_ids[0],
            event_ids[1],
        )

        self.assertEqual(
            PaymentEvent.objects.filter(
                provider=Payment.Provider.MERCADO_PAGO,
                event_id="EVENT-CONCURRENT-001",
            ).count(),
            1,
        )
