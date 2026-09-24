from django.db.models import Prefetch, Q
from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny

from apps.core.pagination import CatalogPagination

from .models import Category, Product, ProductVariant
from .serializers import (
    CategorySerializer,
    ProductSerializer,
)


def _product_queryset():
    active_categories = Category.objects.filter(
        is_active=True,
    )

    active_variants = (
        ProductVariant.objects
        .filter(
            is_active=True,
            color__is_active=True,
            size__is_active=True,
        )
        .select_related(
            "color",
            "size",
        )
    )

    return (
        Product.objects
        .filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "categories",
                queryset=active_categories,
                to_attr="active_categories",
            ),
            Prefetch(
                "variants",
                queryset=active_variants,
                to_attr="active_variants",
            ),
            "images__color",
        )
    )


def _parse_boolean_query_param(value, field_name):
    if value is None:
        return None

    normalized = str(value).strip().lower()

    if normalized in {"true", "1", "yes"}:
        return True

    if normalized in {"false", "0", "no"}:
        return False

    raise serializers.ValidationError(
        {
            field_name: (
                f'Invalid boolean value: "{value}".'
            )
        }
    )


class CategoryListAPIView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(
            is_active=True,
        )


class ProductListAPIView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ProductSerializer
    pagination_class = CatalogPagination

    def get_queryset(self):
        queryset = _product_queryset()

        category = self.request.query_params.get(
            "category"
        )
        search = self.request.query_params.get(
            "search"
        )
        featured = _parse_boolean_query_param(
            self.request.query_params.get("featured"),
            "featured",
        )
        in_stock = _parse_boolean_query_param(
            self.request.query_params.get("in_stock"),
            "in_stock",
        )

        if category:
            queryset = queryset.filter(
                categories__slug=category.strip(),
                categories__is_active=True,
            )

        if search:
            search = search.strip()

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search)
                    | Q(short_description__icontains=search)
                    | Q(description__icontains=search)
                    | Q(variants__sku__icontains=search)
                )

        if featured is not None:
            queryset = queryset.filter(
                is_featured=featured,
            )

        if in_stock is True:
            queryset = queryset.filter(
                variants__is_active=True,
                variants__stock_quantity__gt=0,
                variants__color__is_active=True,
                variants__size__is_active=True,
            )
        elif in_stock is False:
            queryset = queryset.exclude(
                variants__is_active=True,
                variants__stock_quantity__gt=0,
                variants__color__is_active=True,
                variants__size__is_active=True,
            )

        return queryset.distinct()


class ProductDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ProductSerializer
    lookup_field = "slug"

    queryset = _product_queryset()
