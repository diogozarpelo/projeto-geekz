from decimal import Decimal, InvalidOperation

from django.db import transaction

from apps.cart.models import Cart, CartItem
from apps.catalog.models import ProductVariant

from .models import Order, OrderItem


class OrderConversionError(ValueError):
    pass


def _to_decimal(value, field_name):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise OrderConversionError(
            f"{field_name} must be a valid decimal amount."
        ) from exc

    if amount < 0:
        raise OrderConversionError(
            f"{field_name} cannot be negative."
        )

    return amount


@transaction.atomic
def convert_cart_to_order(
    *,
    cart,
    customer_name,
    customer_email,
    shipping_amount=Decimal("0.00"),
    discount_amount=Decimal("0.00"),
    notes="",
):
    if not customer_name or not customer_name.strip():
        raise OrderConversionError("Customer name is required.")

    if not customer_email or not customer_email.strip():
        raise OrderConversionError("Customer email is required.")

    shipping_amount = _to_decimal(
        shipping_amount,
        "Shipping amount",
    )
    discount_amount = _to_decimal(
        discount_amount,
        "Discount amount",
    )

    locked_cart = (
        Cart.objects
        .select_for_update()
        .get(pk=cart.pk)
    )

    if locked_cart.status != Cart.Status.ACTIVE:
        raise OrderConversionError(
            "Only active carts can be converted into orders."
        )

    cart_items = list(
        CartItem.objects
        .filter(cart=locked_cart)
        .select_related(
            "variant__product",
            "variant__color",
            "variant__size",
        )
        .order_by("id")
    )

    if not cart_items:
        raise OrderConversionError(
            "An empty cart cannot be converted into an order."
        )

    variant_ids = [item.variant_id for item in cart_items]

    locked_variants = {
        variant.pk: variant
        for variant in (
            ProductVariant.objects
            .select_for_update()
            .select_related(
                "product",
                "color",
                "size",
            )
            .filter(pk__in=variant_ids)
            .order_by("pk")
        )
    }

    subtotal = Decimal("0.00")
    prepared_items = []

    for cart_item in cart_items:
        variant = locked_variants.get(cart_item.variant_id)

        if variant is None:
            raise OrderConversionError(
                "One of the cart variants no longer exists."
            )

        if not variant.product.is_active:
            raise OrderConversionError(
                f'Product "{variant.product.name}" is inactive.'
            )

        if not variant.is_active:
            raise OrderConversionError(
                f'Variant "{variant.sku}" is inactive.'
            )

        if cart_item.quantity < 1:
            raise OrderConversionError(
                f'Invalid quantity for variant "{variant.sku}".'
            )

        if variant.stock_quantity < cart_item.quantity:
            raise OrderConversionError(
                f'Insufficient stock for variant "{variant.sku}".'
            )

        unit_price = variant.effective_price
        line_total = unit_price * cart_item.quantity
        subtotal += line_total

        prepared_items.append(
            {
                "variant": variant,
                "product_name": variant.product.name,
                "sku": variant.sku,
                "color_name": variant.color.name,
                "size_name": variant.size.name,
                "unit_price": unit_price,
                "quantity": cart_item.quantity,
            }
        )

    total_before_discount = subtotal + shipping_amount

    if discount_amount > total_before_discount:
        raise OrderConversionError(
            "Discount amount cannot exceed the order total."
        )

    total_amount = total_before_discount - discount_amount

    order = Order.objects.create(
        user_id=locked_cart.user_id,
        customer_name=customer_name.strip(),
        customer_email=customer_email.strip(),
        subtotal=subtotal,
        shipping_amount=shipping_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        notes=notes.strip(),
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                variant=item["variant"],
                product_name=item["product_name"],
                sku=item["sku"],
                color_name=item["color_name"],
                size_name=item["size_name"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
            )
            for item in prepared_items
        ]
    )

    for item in prepared_items:
        variant = item["variant"]
        variant.stock_quantity -= item["quantity"]
        variant.save(
            update_fields=(
                "stock_quantity",
                "updated_at",
            )
        )

    locked_cart.status = Cart.Status.CONVERTED
    locked_cart.save(
        update_fields=(
            "status",
            "updated_at",
        )
    )

    return order
