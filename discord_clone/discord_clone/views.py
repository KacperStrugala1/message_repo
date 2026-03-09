from django.http import HttpResponse
from django.views import View
from django.shortcuts import redirect, render
from .utils import socket_connect as sc


class WelcomeView(View):
    template_name = "welcome.html"

    def get(self, request):

        return render(request, self.template_name)

class HomeView(View):
    template_name = "home.html"

    def get(self, request):

        return render(request, self.template_name)

    def post(self, request):
        return redirect("channel_view")


class LoginView(View):
    template_name = "login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        return redirect("home_view")


class ChannelView(View):
    template_name = "channel.html"
    #connect to socket


    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        pass