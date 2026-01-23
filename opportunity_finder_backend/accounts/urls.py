from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    DeleteAccountView,
    EmailTokenObtainPairView,
    LogoutAllView,
    LogoutView,
    MeView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    SubscriptionUpgradeRequestAdminListView,
    SubscriptionUpgradeRequestListCreateView,
    SubscriptionUpgradeRequestReviewView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout/all/", LogoutAllView.as_view(), name="logout_all"),
    path("me/", MeView.as_view(), name="me"),
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("account/delete/", DeleteAccountView.as_view(), name="account_delete"),
    path("subscription/requests/", SubscriptionUpgradeRequestListCreateView.as_view(), name="subscription_requests"),
    path("subscription/requests/admin/", SubscriptionUpgradeRequestAdminListView.as_view(), name="subscription_requests_admin"),
    path("subscription/requests/<int:pk>/review/", SubscriptionUpgradeRequestReviewView.as_view(), name="subscription_requests_review"),
]


