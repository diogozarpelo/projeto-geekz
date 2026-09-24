from django.contrib.auth import get_user_model
from django.db import transaction

from apps.catalog.models import ProductVariant

from .models import Cart, CartItem


class CartError(ValueError):
    pass


def _validate_quantity(quantity):
    if not isinstance(quantity, int) or quantity < 1:
        raise CartError(
            "Cart item quantity must be at least 1."
        )

    return quantity


def _ensure_active_cart(cart):
    if cart.status != Cart.Status.ACTIVE:
        raise CartError(
            "Only active carts can be modified."
        )


def _ensure_purchasable_variant(variant):
    if not variant.product.is_active:
        raise CartError(
            "This product is not available."
        )

    if not variant.is_active:
        raise CartError(
            "This product variant is not available."
        )

    if not variant.color.is_active:
        raise CartError(
            "This product color is not available."
        )

    if not variant.size.is_active:
        raise CartError(
            "This product size is not available."
        )


@transaction.atomic
def get_or_create_active_cart(*, user):
    user_model = get_user_model()

    locked_user = (
        user_model.objects
        .select_for_update()
        .get(pk=user.pk)
    )

    cart = (
        Cart.objects
        .select_for_update()
        .filter(
            user=locked_user,
            status=Cart.Status.ACTIVE,
        )
        .first()
    )

    if cart is not None:
        return cart

    return Cart.objects.create(
        user=locked_user,
        status=Cart.Status.ACTIVE,
    )


@transaction.atomic
def add_variant_to_cart(
    *,
    cart,
    variant,
    quantity=1,
):
    quantity = _validate_quantity(quantity)

    locked_cart = (
        Cart.objects
        .select_for_update()
        .get(pk=cart.pk)
    )

    _ensure_active_cart(locked_cart)

    locked_variant = (
        ProductVariant.objects
        .select_for_update()
        .select_related(
            "product",
            "color",
            "size",
        )
        .get(pk=variant.pk)
    )

    _ensure_purchasable_variant(
        locked_variant
    )

    cart_item = (
        CartItem.objects
        .select_for_update()
        .filter(
            cart=locked_cart,
            variant=locked_variant,
        )
        .first()
    )

    current_quantity = (
        cart_item.quantity
        if cart_item is not None
        else 0
    )

    target_quantity = (
        current_quantity + quantity
    )

    if target_quantity > locked_variant.stock_quantity:
        raise CartError(
            "Requested quantity exceeds available stock."
        )

    if cart_item is None:
        cart_item = CartItem.objects.create(
            cart=locked_cart,
            variant=locked_variant,
            quantity=target_quantity,
        )
    else:
        cart_item.quantity = target_quantity
        cart_item.save(
            update_fields=(
                "quantity",
                "updated_at",
            )
        )

    return cart_item


@transaction.atomic
def update_cart_item_quantity(
    *,
    item,
    quantity,
):
    quantity = _validate_quantity(quantity)

    locked_cart = (
        Cart.objects
        .select_for_update()
        .get(pk=item.cart_id)
    )

    _ensure_active_cart(locked_cart)

    locked_variant = (
        ProductVariant.objects
        .select_for_update()
        .select_related(
            "product",
            "color",
            "size",
        )
        .get(pk=item.variant_id)
    )

    _ensure_purchasable_variant(
        locked_variant
    )

    locked_item = (
        CartItem.objects
        .select_for_update()
        .get(
            pk=item.pk,
            cart=locked_cart,
        )
    )

    if quantity > locked_variant.stock_quantity:
        raise CartError(
            "Requested quantity exceeds available stock."
        )

    if locked_item.quantity != quantity:
        locked_item.quantity = quantity
        locked_item.save(
            update_fields=(
                "quantity",
                "updated_at",
            )
        )

    return locked_item


@transaction.atomic
def remove_cart_item(*, item):
    locked_cart = (
        Cart.objects
        .select_for_update()
        .get(pk=item.cart_id)
    )

    _ensure_active_cart(locked_cart)

    locked_item = (
        CartItem.objects
        .select_for_update()
        .get(
            pk=item.pk,
            cart=locked_cart,
        )
    )

    locked_item.delete()
