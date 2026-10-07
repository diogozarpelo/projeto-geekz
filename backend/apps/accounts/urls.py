from django.urls import path

from .views import (
    CurrentUserAddressAPIView,
    CurrentUserAPIView,
    LoginAPIView,
    LogoutAPIView,
    PasswordChangeAPIView,
    RegisterAPIView,
)


app_name = "accounts"


urlpatterns = [
    path(
        "register/",
        RegisterAPIView.as_view(),
        name="register",
    ),
    path(
        "login/",
        LoginAPIView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        LogoutAPIView.as_view(),
        name="logout",
    ),
    path(
        "password/change/",
        PasswordChangeAPIView.as_view(),
        name="password-change",
    ),    path(
        "me/address/",
        CurrentUserAddressAPIView.as_view(),
        name="me-address",
    ),    path(
        "me/",
        CurrentUserAPIView.as_view(),
        name="me",
    ),
]
