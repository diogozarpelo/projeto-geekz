import uuid

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


def _parse_cart_public_id(public_id):
    if not public_id:
        return None

    try:
        return uuid.UUID(str(public_id))
    except (TypeError, ValueError, AttributeError):
        return None


@transaction.atomic
def get_or_create_anonymous_cart(*, public_id=None):
    parsed_public_id = _parse_cart_public_id(
        public_id
    )

    if parsed_public_id is not None:
        cart = (
            Cart.objects
            .select_for_update()
            .filter(
                public_id=parsed_public_id,
                user__isnull=True,
                status=Cart.Status.ACTIVE,
            )
            .first()
        )

        if cart is not None:
            return cart

    return Cart.objects.create(
        user=None,
        status=Cart.Status.ACTIVE,
    )


@transaction.atomic
def merge_anonymous_cart_into_user(
    *,
    user,
    anonymous_public_id,
):
    target_cart = get_or_create_active_cart(
        user=user
    )

    parsed_public_id = _parse_cart_public_id(
        anonymous_public_id
    )

    if parsed_public_id is None:
        return target_cart

    anonymous_cart = (
        Cart.objects
        .select_for_update()
        .filter(
            public_id=parsed_public_id,
            user__isnull=True,
            status=Cart.Status.ACTIVE,
        )
        .first()
    )

    if anonymous_cart is None:
        return target_cart

    anonymous_items = list(
        CartItem.objects
        .select_for_update()
        .select_related(
            "variant",
            "variant__product",
            "variant__color",
            "variant__size",
        )
        .filter(cart=anonymous_cart)
    )

    for anonymous_item in anonymous_items:
        variant = anonymous_item.variant

        try:
            _ensure_purchasable_variant(
                variant
            )
        except CartError:
            continue

        target_item = (
            CartItem.objects
            .select_for_update()
            .filter(
                cart=target_cart,
                variant=variant,
            )
            .first()
        )

        current_quantity = (
            target_item.quantity
            if target_item is not None
            else 0
        )

        target_quantity = min(
            current_quantity
            + anonymous_item.quantity,
            variant.stock_quantity,
        )

        if target_quantity < 1:
            continue

        if target_item is None:
            CartItem.objects.create(
                cart=target_cart,
                variant=variant,
                quantity=target_quantity,
            )
        elif target_item.quantity != target_quantity:
            target_item.quantity = target_quantity
            target_item.save(
                update_fields=(
                    "quantity",
                    "updated_at",
                )
            )

    anonymous_cart.status = Cart.Status.ABANDONED
    anonymous_cart.save(
        update_fields=(
            "status",
            "updated_at",
        )
    )

    return target_cart


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
