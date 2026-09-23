from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import ProductVariant

from .models import Cart, CartItem
from .serializers import (
    AddCartItemSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)
from .services import (
    CartError,
    add_variant_to_cart,
    get_or_create_active_cart,
    remove_cart_item,
    update_cart_item_quantity,
)


def _load_cart_for_response(cart):
    return (
        Cart.objects
        .prefetch_related(
            "items__variant__product",
            "items__variant__color",
            "items__variant__size",
        )
        .get(pk=cart.pk)
    )


class ActiveCartAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        cart = get_or_create_active_cart(
            user=request.user,
        )

        cart = _load_cart_for_response(cart)

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )


class CartItemCreateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = AddCartItemSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        cart = get_or_create_active_cart(
            user=request.user,
        )

        variant = get_object_or_404(
            ProductVariant.objects.select_related(
                "product",
                "color",
                "size",
            ),
            pk=serializer.validated_data["variant_id"],
        )

        try:
            add_variant_to_cart(
                cart=cart,
                variant=variant,
                quantity=serializer.validated_data[
                    "quantity"
                ],
            )
        except CartError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc

        cart = _load_cart_for_response(cart)

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )


class CartItemDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def _get_item(self, request, item_id):
        return get_object_or_404(
            CartItem.objects.select_related(
                "cart",
                "variant",
            ),
            pk=item_id,
            cart__user=request.user,
            cart__status=Cart.Status.ACTIVE,
        )

    def patch(self, request, item_id):
        item = self._get_item(
            request,
            item_id,
        )

        serializer = UpdateCartItemSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        try:
            updated_item = update_cart_item_quantity(
                item=item,
                quantity=serializer.validated_data[
                    "quantity"
                ],
            )
        except CartError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc

        cart = _load_cart_for_response(
            updated_item.cart
        )

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, item_id):
        item = self._get_item(
            request,
            item_id,
        )
        cart = item.cart

        try:
            remove_cart_item(
                item=item,
            )
        except CartError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc

        cart = _load_cart_for_response(cart)

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )
