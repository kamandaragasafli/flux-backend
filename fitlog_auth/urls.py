from django.urls import path

from . import views

urlpatterns = [
    path("auth/register/", views.register, name="fitlog-register"),
    path("auth/login/", views.login, name="fitlog-login"),
    path("auth/google/", views.google_auth, name="fitlog-google"),
    path("auth/me/", views.me, name="fitlog-me"),
]
