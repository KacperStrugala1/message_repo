from django.http import HttpResponse
from django.views import View
from django.shortcuts import redirect, render
from django.http import JsonResponse
from .utils import socket_connect as sc
from .models import Message
from . import protocols
import socket
import struct


class WelcomeView(View):
    template_name = "welcome.html"

    def get(self, request):

        return render(request, self.template_name)
    
    def post(self, request):
        return redirect("login_view")



class LoginView(View):
    template_name = "login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        return redirect("channel_view")


class ChannelView(View):
    template_name = "channel.html"

    
    def get(self, request):
        
        return render(request, self.template_name)
    
class ApiView(View):
    def get(self, request):
        messages = Message.objects.order_by("timestamp")[:10]

        messages_data = []
        for message in messages:
            messages_data.append({
                "source": message.source,
                "content": message.content
            })

        return JsonResponse({"messages": messages_data})
