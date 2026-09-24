from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
        )
        read_only_fields = (
            "id",
            "email",
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        validators=(validate_password,),
    )
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        )
        extra_kwargs = {
            "first_name": {
                "required": False,
                "allow_blank": True,
            },
            "last_name": {
                "required": False,
                "allow_blank": True,
            },
        }

    def validate_email(self, value):
        email = User.objects.normalize_email(value)

        if User.objects.filter(
            email__iexact=email,
        ).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "Password confirmation does not match."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop(
            "password_confirm"
        )
        password = validated_data.pop(
            "password"
        )

        try:
            return User.objects.create_user(
                password=password,
                **validated_data,
            )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {
                    "email": (
                        "A user with this email already exists."
                    )
                }
            ) from exc


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate_email(self, value):
        return User.objects.normalize_email(value)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"],
            password=attrs["password"],
        )

        if user is None:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Invalid email or password."
                    )
                }
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "This account is inactive."
                    )
                }
            )

        attrs["user"] = user
        return attrs
