from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart

from .models import Order
from .payment_services import PaymentError, create_payment_attempt
from .serializers import (
    CheckoutSerializer,
    OrderSerializer,
    PaymentAttemptSerializer,
    PaymentSerializer,
)
from .services import OrderConversionError, convert_cart_to_order


class CheckoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = CheckoutSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        checkout_data = dict(
            serializer.validated_data
        )
        cart_public_id = checkout_data.pop(
            "cart_public_id"
        )

        cart = get_object_or_404(
            Cart,
            public_id=cart_public_id,
            user=request.user,
        )

        try:
            order = convert_cart_to_order(
                cart=cart,
                **checkout_data,
            )
        except OrderConversionError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, public_id):
        order = get_object_or_404(
            Order.objects.prefetch_related(
                "items",
                "payments",
            ),
            public_id=public_id,
            user=request.user,
        )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK,
        )


class PaymentAttemptAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, public_id):
        order = get_object_or_404(
            Order,
            public_id=public_id,
            user=request.user,
        )

        serializer = PaymentAttemptSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        try:
            payment = create_payment_attempt(
                order=order,
                method=serializer.validated_data[
                    "method"
                ],
            )
        except PaymentError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK,
        )
