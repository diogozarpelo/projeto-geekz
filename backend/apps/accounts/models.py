from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        normalized = super().normalize_email(email)

        if normalized is None:
            return None

        return normalized.strip().lower()

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuários precisam ter is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuários precisam ter is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_user_email_ci",
            ),
        ]

    def __str__(self):
        return self.email

class UserAddress(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="address",
    )
    postal_code = models.CharField(
        max_length=20,
    )
    street = models.CharField(
        max_length=180,
    )
    number = models.CharField(
        max_length=30,
    )
    complement = models.CharField(
        max_length=120,
        blank=True,
        default="",
    )
    neighborhood = models.CharField(
        max_length=120,
    )
    city = models.CharField(
        max_length=120,
    )
    state = models.CharField(
        max_length=80,
    )
    country = models.CharField(
        max_length=80,
        default="BR",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.user.email} - "
            f"{self.city}/{self.state}"
        )
