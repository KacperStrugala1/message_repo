from django.http import HttpResponse
from django.views import View
from django.shortcuts import redirect, render


class HomeView(View):
    template_name = "home.html"

    def get(self, request):

        return render(request, self.template_name)


class LoginView(View):
    template_name = "login.html"

    def get(self, request):
        return render(request, self.template_name)


class RegisterView(View):
    template_name = "register.html"

    def get(self, request):
        return render(request, self.template_name)
