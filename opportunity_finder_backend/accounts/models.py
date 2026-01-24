from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(DjangoUserManager):
    """
    Custom manager for email-based authentication while still using AbstractUser.
    """

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("The email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    USER = "USER", "User"
    MODERATOR = "MODERATOR", "Moderator"
    ADMIN = "ADMIN", "Admin"
    SUPPORT = "SUPPORT", "Support"


class SubscriptionLevel(models.TextChoices):
    STANDARD = "STANDARD", "Standard"
    PREMIUM = "PREMIUM", "Premium"


class User(AbstractUser):
    """
    Email-first user model.

    We intentionally ignore username; profile fields (name, etc.) will live in a separate profile model.
    """

    username = None  # remove the username field entirely
    first_name = None  # name fields belong in UserProfile (not auth user)
    last_name = None
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
        help_text="User role for access control",
    )
    subscription_level = models.CharField(
        max_length=20,
        choices=SubscriptionLevel.choices,
        default=SubscriptionLevel.STANDARD,
        help_text="Subscription tier for access control",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def get_full_name(self) -> str:
        """
        AbstractUser expects first_name/last_name; we removed them.
        Keep Django admin/third-party integrations safe by providing a fallback.
        """
        return self.email

    def get_short_name(self) -> str:
        return self.email

    def __str__(self) -> str:
        return self.email


class SubscriptionUpgradeRequest(models.Model):
    class IntervalPeriod(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscription_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payment_method = models.CharField(max_length=50, default="Telebirr")
    interval_period = models.CharField(
        max_length=20,
        choices=IntervalPeriod.choices,
        default=IntervalPeriod.MONTHLY,
    )
    receipt = models.FileField(upload_to="subscription_receipts/", blank=True)
    note = models.TextField(blank=True, default="")
    admin_note = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_subscription_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"SubscriptionUpgradeRequest<{self.user_id}:{self.status}>"
