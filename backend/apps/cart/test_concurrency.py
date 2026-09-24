from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase

from .models import Cart
from .services import get_or_create_active_cart


class ActiveCartConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="cart-concurrency@example.com",
            password="StrongPass123!",
        )

    def _create_cart(self, barrier):
        connection.close()

        try:
            user = get_user_model().objects.get(
                pk=self.user.pk,
            )

            barrier.wait(timeout=10)

            cart = get_or_create_active_cart(
                user=user,
            )

            return cart.pk
        finally:
            connection.close()

    def test_concurrent_requests_reuse_the_same_active_cart(self):
        barrier = Barrier(2)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    self._create_cart,
                    barrier,
                )
                for _ in range(2)
            ]

            cart_ids = [
                future.result(timeout=15)
                for future in futures
            ]

        self.assertEqual(
            cart_ids[0],
            cart_ids[1],
        )

        self.assertEqual(
            Cart.objects.filter(
                user=self.user,
                status=Cart.Status.ACTIVE,
            ).count(),
            1,
        )
