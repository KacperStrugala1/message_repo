from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.WelcomeView.as_view(), name="welcome_view"),
    path("home", views.HomeView.as_view(), name="home_view"),
    path("login", views.LoginView.as_view(), name="login_view"),
    path("channel", views.ChannelView.as_view(), name="channel_view"),
]
