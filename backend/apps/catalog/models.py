from decimal import Decimal

from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from .validators import validate_product_image_size


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    hex_code = models.CharField(max_length=7, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=30, unique=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "name")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(compare_at_price__isnull=True)
                    | models.Q(compare_at_price__gte=models.F("base_price"))
                ),
                name="compare_at_price_gte_base_price",
            ),
        ]

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name="product_variants",
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.PROTECT,
        related_name="product_variants",
    )
    sku = models.CharField(max_length=80, unique=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("product", "color", "size")
        constraints = [
            models.UniqueConstraint(
                fields=("product", "color", "size"),
                name="unique_product_color_size",
            ),
        ]

    @property
    def effective_price(self):
        return self.price if self.price is not None else self.product.base_price

    @property
    def is_in_stock(self):
        return self.is_active and self.stock_quantity > 0

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        related_name="product_images",
        null=True,
        blank=True,
    )
    image = models.ImageField(
        upload_to="products/%Y/%m/",
        validators=(
            FileExtensionValidator(
                allowed_extensions=(
                    "jpg",
                    "jpeg",
                    "png",
                    "webp",
                    "gif",
                )
            ),
            validate_product_image_size,
        ),
    )
    alt_text = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("product",),
                condition=models.Q(is_primary=True),
                name="unique_primary_image_per_product",
            ),
        ]

    def __str__(self):
        return f"Image - {self.product.name}"
