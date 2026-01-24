from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from .models import SubscriptionUpgradeRequest


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "password", "password2")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        # Enforce Django password validators (common password, similarity, etc.)
        try:
            validate_password(
                password=attrs.get("password"),
                user=User(email=attrs.get("email")),
            )
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("new_password2"):
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})

        try:
            validate_password(password=attrs.get("new_password"))
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "is_active", "role", "subscription_level")
        read_only_fields = fields


class SubscriptionUpgradeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionUpgradeRequest
        fields = (
            "id",
            "status",
            "payment_method",
            "interval_period",
            "receipt",
            "note",
            "admin_note",
            "reviewed_at",
            "created_at",
        )
        read_only_fields = ("id", "status", "admin_note", "reviewed_at", "created_at")


class SubscriptionUpgradeRequestCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.CharField(required=False, default="Telebirr")
    interval_period = serializers.CharField(
        required=False,
        default=SubscriptionUpgradeRequest.IntervalPeriod.MONTHLY,
    )

    class Meta:
        model = SubscriptionUpgradeRequest
        fields = ("payment_method", "interval_period", "receipt", "note")


class SubscriptionUpgradeRequestReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionUpgradeRequest
        fields = ("status", "admin_note")

    def validate_status(self, value):
        if value not in [
            SubscriptionUpgradeRequest.Status.APPROVED,
            SubscriptionUpgradeRequest.Status.REJECTED,
        ]:
            raise serializers.ValidationError("Status must be APPROVED or REJECTED.")
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs.get("current_password")):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})

        try:
            validate_password(password=attrs.get("new_password"), user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if attrs.get("confirm", "").strip().upper() != "DELETE":
            raise serializers.ValidationError({"confirm": "Type DELETE to confirm account removal."})

        if not user.check_password(attrs.get("password")):
            raise serializers.ValidationError({"password": "Password is incorrect."})

        return attrs


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Uses USERNAME_FIELD from the configured user model (email).
    """

    # No changes required; this class exists to make intent explicit and future-proof.
    pass


