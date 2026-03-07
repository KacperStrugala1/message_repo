from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.HomeView.as_view(), name="home_view"),
    path("login", views.LoginView.as_view(), name="login_view"),
    path("register", views.RegisterView.as_view(), name="register_view"),
]
