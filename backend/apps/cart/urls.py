from django.urls import path

from .views import (
    ActiveCartAPIView,
    CartItemCreateAPIView,
    CartItemDetailAPIView,
)


app_name = "cart"


urlpatterns = [
    path(
        "",
        ActiveCartAPIView.as_view(),
        name="active-cart",
    ),
    path(
        "items/",
        CartItemCreateAPIView.as_view(),
        name="item-create",
    ),
    path(
        "items/<int:item_id>/",
        CartItemDetailAPIView.as_view(),
        name="item-detail",
    ),
]
