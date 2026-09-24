import hashlib

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mercadopago.webhook import (
    InvalidWebhookSignatureError,
    WebhookSignatureValidator,
)

from apps.cart.models import Cart
from apps.core.pagination import OrderHistoryPagination

from .models import Order, Payment
from .payment_event_services import (
    PaymentEventError,
    process_normalized_payment_event,
)
from .payment_services import PaymentError, create_payment_attempt
from .providers.mercado_pago import (
    MercadoPagoError,
    MercadoPagoProvider,
    normalize_order_status,
)
from .serializers import (
    CheckoutSerializer,
    OrderSerializer,
    PaymentAttemptSerializer,
    PaymentSerializer,
)
from .services import OrderConversionError, convert_cart_to_order


class PaymentProviderUnavailable(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Payment provider is temporarily unavailable."
    default_code = "payment_provider_unavailable"


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


class OrderListAPIView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer
    pagination_class = OrderHistoryPagination

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "items",
                "payments",
            )
            .order_by("-created_at")
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

        if payment.method == Payment.Method.PIX:
            try:
                payment = MercadoPagoProvider().create_pix_order(
                    payment=payment,
                )
            except MercadoPagoError as exc:
                raise PaymentProviderUnavailable(
                    str(exc)
                ) from exc

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK,
        )


class MercadoPagoWebhookAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def _validate_signature(
        self,
        request,
        provider_order_id,
    ):
        secret = (
            settings.MERCADO_PAGO_WEBHOOK_SECRET
        )

        if not secret:
            raise PaymentProviderUnavailable(
                "Mercado Pago webhook secret is not configured."
            )

        try:
            WebhookSignatureValidator.validate(
                request.headers.get(
                    "x-signature"
                ),
                request.headers.get(
                    "x-request-id"
                ),
                provider_order_id,
                secret,
                tolerance_seconds=(
                    settings.MERCADO_PAGO_WEBHOOK_TOLERANCE_SECONDS
                ),
            )
        except InvalidWebhookSignatureError as exc:
            return False

        return True

    def _event_id(
        self,
        *,
        provider_order_id,
        payload,
    ):
        notification_id = str(
            payload.get("id") or ""
        ).strip()

        if notification_id:
            return notification_id

        action = str(
            payload.get("action") or ""
        )
        date_created = str(
            payload.get("date_created") or ""
        )

        data = payload.get("data") or {}

        source = "|".join(
            (
                provider_order_id,
                action,
                str(data.get("status") or ""),
                str(
                    data.get("status_detail")
                    or ""
                ),
                date_created,
            )
        )

        return hashlib.sha256(
            source.encode("utf-8")
        ).hexdigest()

    def post(self, request):
        provider_order_id = str(
            request.query_params.get(
                "data.id"
            )
            or ""
        ).strip()

        notification_type = str(
            request.query_params.get(
                "type"
            )
            or ""
        ).strip().lower()

        if not self._validate_signature(
            request,
            provider_order_id or None,
        ):
            return Response(
                {
                    "detail": (
                        "Invalid Mercado Pago webhook signature."
                    )
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not provider_order_id:
            return Response(
                {
                    "detail": (
                        "Mercado Pago order ID is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if notification_type not in {
            "order",
            "orders_v2",
        }:
            return Response(
                {
                    "detail": (
                        "Unsupported Mercado Pago notification type."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = (
            request.data
            if isinstance(request.data, dict)
            else {}
        )

        payment = (
            Payment.objects
            .filter(
                provider=Payment.Provider.MERCADO_PAGO,
                provider_order_id=provider_order_id,
            )
            .first()
        )

        if payment is None:
            return Response(
                {
                    "detail": (
                        "Mercado Pago payment was not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            provider_order = (
                MercadoPagoProvider().get_order(
                    provider_order_id=provider_order_id,
                )
            )
        except MercadoPagoError as exc:
            raise PaymentProviderUnavailable(
                str(exc)
            ) from exc

        external_reference = str(
            provider_order.get(
                "external_reference"
            )
            or ""
        ).strip()

        if (
            external_reference
            and external_reference
            != str(payment.order.public_id)
        ):
            return Response(
                {
                    "detail": (
                        "Mercado Pago order reference does not "
                        "match the local order."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        transactions = (
            provider_order.get(
                "transactions"
            )
            or {}
        )
        provider_payments = (
            transactions.get(
                "payments"
            )
            or []
        )

        if not provider_payments:
            return Response(
                {
                    "detail": (
                        "Mercado Pago order has no payment transaction."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        provider_payment = (
            provider_payments[0]
        )

        external_payment_id = str(
            provider_payment.get("id")
            or ""
        ).strip()

        if not external_payment_id:
            return Response(
                {
                    "detail": (
                        "Mercado Pago payment ID is missing."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        if (
            payment.external_id
            and payment.external_id
            != external_payment_id
        ):
            return Response(
                {
                    "detail": (
                        "Mercado Pago payment ID does not match "
                        "the local payment."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        provider_status = str(
            provider_order.get("status")
            or ""
        ).strip()

        provider_status_detail = str(
            provider_order.get(
                "status_detail"
            )
            or ""
        ).strip()

        try:
            normalized_status = (
                normalize_order_status(
                    provider_status,
                    provider_status_detail,
                )
            )
        except MercadoPagoError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        payment.provider_order_id = (
            provider_order_id
        )
        payment.external_id = (
            external_payment_id
        )

        provider_data = dict(
            payment.provider_data
            or {}
        )
        provider_data.update(
            {
                "order_status": (
                    provider_status
                ),
                "order_status_detail": (
                    provider_status_detail
                ),
                "payment_status": str(
                    provider_payment.get(
                        "status"
                    )
                    or ""
                ),
                "payment_status_detail": str(
                    provider_payment.get(
                        "status_detail"
                    )
                    or ""
                ),
            }
        )

        payment.provider_data = (
            provider_data
        )
        payment.save(
            update_fields=(
                "provider_order_id",
                "external_id",
                "provider_data",
                "updated_at",
            )
        )

        event_id = self._event_id(
            provider_order_id=provider_order_id,
            payload=payload,
        )

        try:
            process_normalized_payment_event(
                payment=payment,
                provider=(
                    Payment.Provider.MERCADO_PAGO
                ),
                event_id=event_id,
                event_type=str(
                    payload.get("action")
                    or "order.updated"
                ),
                external_payment_id=(
                    external_payment_id
                ),
                external_status=(
                    normalized_status
                ),
                payload=payload,
            )
        except PaymentEventError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"status": "ok"},
            status=status.HTTP_200_OK,
        )
