from django.contrib.auth import get_user_model, logout as django_logout
from django.db import transaction

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


User = get_user_model()


@transaction.atomic
def _rotate_token(user):
    locked_user = (
        User.objects
        .select_for_update()
        .get(pk=user.pk)
    )

    Token.objects.filter(
        user=locked_user,
    ).delete()

    return Token.objects.create(
        user=locked_user,
    )


class RegisterAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.save()

        token, _ = Token.objects.get_or_create(
            user=user,
        )

        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )
        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.validated_data["user"]

        token = _rotate_token(
            user
        )

        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        Token.objects.filter(
            user=request.user,
        ).delete()

        django_logout(
            request
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class CurrentUserAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(
            raise_exception=True,
        )
        user = serializer.save()

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK,
        )
