from django.core.management.base import BaseCommand
from django.utils import timezone
from discord_clone.models import Message
from datetime import datetime
import time
import socket
import struct


HOST = "127.0.0.1"
PORT = 9999

TYPE_SUCCESS   = 0x01
TYPE_ERROR     = 0x02
TYPE_HANDSHAKE = 0x03
TYPE_AUTH      = 0x04
TYPE_MESSAGE   = 0x05


def recv_exact(sock, length):
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise Exception("EOF")
        data += chunk
    return data

def encode_string(s):
    data = s.encode("utf-8")
    return struct.pack("!H", len(data)) + data

def decode_string(payload, offset):
    length = struct.unpack_from("!H", payload, offset)[0]
    offset += 2
    text = payload[offset:offset+length].decode("utf-8")
    return text, offset + length


def send_handshake(sock):
    payload = struct.pack("!BBB", 0, 2, 1)  # major, minor, conn_type
    packet = struct.pack("!BH", TYPE_HANDSHAKE, len(payload)) + payload
    sock.sendall(packet)

def send_auth(sock, user, password):
    payload = encode_string(user) + encode_string(password)
    packet = struct.pack("!BH", TYPE_AUTH, len(payload)) + payload
    sock.sendall(packet)

def send_message(sock, source, target, content):
    payload = (
        encode_string(source) +
        encode_string(target) +
        struct.pack("!Q", int(time.time())) +
        encode_string(content)
    )
    packet = struct.pack("!BH", TYPE_MESSAGE, len(payload)) + payload
    sock.sendall(packet)



def parse_message(payload):
    offset = 0

    source, offset = decode_string(payload, offset)
    target, offset = decode_string(payload, offset)

    timestamp = struct.unpack_from("!Q", payload, offset)[0]
    
    offset += 8


    try:
        if timestamp > 32503680000: 
            sekundy = timestamp / 1000.0
        else:
            sekundy = timestamp

        date_time_field = timezone.datetime.fromtimestamp(sekundy, tz=timezone.get_current_timezone())
        
    except (OverflowError, ValueError, OSError):
        
        print(f"Failed with timestamp, Timestamp value: {timestamp}. Set the actual time")
        date_time_field = timezone.now()

    content, offset = decode_string(payload, offset)


    Message.objects.create(
        source = source,
        target = target,
        timestamp = date_time_field,
        content = content
    )

def handle_packet(sock):
    header = recv_exact(sock, 3)

    type_payload = header[0]
    length = struct.unpack("!H", header[1:])[0]

    payload = recv_exact(sock, length)

    if type_payload == TYPE_SUCCESS:
        print("Polaczono do serwera")

    elif type_payload == TYPE_ERROR:
        error_code = payload[0]
        print(f"ERROR: {error_code}")

    elif type_payload == TYPE_MESSAGE:
        parse_message(payload)

    elif type_payload == TYPE_HANDSHAKE:
        proto_major = payload[0]
        proto_minor = payload[1]

    else:
        print(f" UNKNOWN TYPE: {type_payload}")


class Command(BaseCommand):
    help = 'Starting new TCP server'

    def handle(self, *args, **options):
        self.stdout.write("Starting TCP...")
    
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))

            send_handshake(sock)
            send_auth(sock, "kacper", "valid")  

            while True:
                handle_packet(sock)

    