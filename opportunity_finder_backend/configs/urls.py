from django.urls import path

from .views import MyConfigView


urlpatterns = [
    path("me/", MyConfigView.as_view(), name="my-config"),
]


