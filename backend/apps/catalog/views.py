from django.db.models import Q
from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductSerializer,
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

    def get_queryset(self):
        queryset = (
            Product.objects
            .filter(is_active=True)
            .prefetch_related(
                "categories",
                "variants__color",
                "variants__size",
                "images__color",
            )
        )

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

    queryset = (
        Product.objects
        .filter(is_active=True)
        .prefetch_related(
            "categories",
            "variants__color",
            "variants__size",
            "images__color",
        )
    )
