from django.http import HttpResponse
from django.views import View
from django.shortcuts import redirect, render
from .utils import socket_connect as sc
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
    #connect to socket


    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        with protocols.client as s:
            try:
                s.connect((protocols.HOST, protocols.PORT))

                #we want to recive 3 bytes to read type and payload length
                header = protocols.get_data_type_and_length(s, 3)
                type_payload = header[0]
                length = struct.unpack("!H", header[1:])[0]

                payload = protocols.get_data_type_and_length(s, length)

                print("get handshake")
                protocols.send_handshake()
                protocols.send_auth()
                while True:
                    
                    protocols.recive_type(s)

            
            except Exception as exc:
                print(f"Exception: {exc}")