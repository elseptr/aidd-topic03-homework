from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    path("auth/", views.auth_view, name="auth"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
]
