from django.core.management.base import BaseCommand
from django.utils import timezone
from discord_clone.models import Message
from datetime import datetime
import ssl
import time
import socket
import struct


HOST = "rctt.net"
PORT = 9999
SERVER_DOMAIN = "rctt.net"
AUTH_USER = f"kacper@{SERVER_DOMAIN}"
AUTH_PASSWORD = "SnKpJmnSgkwW"

TYPE_SUCCESS   = 0x01
TYPE_ERROR     = 0x02
TYPE_HANDSHAKE = 0x03
TYPE_AUTH      = 0x04
TYPE_MESSAGE   = 0x05
TYPE_LIST      = 0x06
TYPE_USERMODE  = 0x07
TYPE_HISTORY   = 0x08


def cli(message):
    print(message, flush=True)


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


def normalize_addr(addr):
    try:
        user, host = addr.split("@", 1)
    except ValueError:
        return addr if "@" in addr else f"{addr}@{SERVER_DOMAIN}"

    return f"{user}@{SERVER_DOMAIN}"


def create_connection(host, port, use_tls=True):
    raw_socket = socket.create_connection((host, port))

    if use_tls is False:
        return raw_socket

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        return context.wrap_socket(raw_socket, server_hostname=SERVER_DOMAIN)
    except ssl.SSLError:
        raw_socket.close()

        raise


def auth_user(username):
    return normalize_addr(username).split("@", 1)[0]

def decode_string(payload, offset):
    length = struct.unpack_from("!H", payload, offset)[0]
    offset += 2
    text = payload[offset:offset+length].decode("utf-8")
    return text, offset + length


def send_handshake(sock):
    cli("sending handshake packet")
    payload = struct.pack("!BBB", 0, 1, 1)  # major, minor, conn_type
    packet = struct.pack("!BH", TYPE_HANDSHAKE, len(payload)) + payload
    sock.sendall(packet)

def send_auth(sock, user, password):
    cli(f"sending auth packet as {user}")
    payload = encode_string(user) + encode_string(password)
    packet = struct.pack("!BH", TYPE_AUTH, len(payload)) + payload
    sock.sendall(packet)

def send_message(sock, source, target, content, timestamp=None):
    source = normalize_addr(source)
    target = normalize_addr(target)
    if timestamp is None:
        timestamp = int(time.time())
    payload = (
        encode_string(source) +
        encode_string(target) +
        struct.pack("!Q", timestamp) +
        encode_string(content)
    )
    packet = struct.pack("!BH", TYPE_MESSAGE, len(payload)) + payload
    cli(
        "sending message packet "
        f"source={source} target={target} timestamp={timestamp} content={content}"
    )
    cli(f"sending raw packet bytes {packet.hex()}")
    sock.sendall(packet)
    return timestamp


def get_history_packet(channel_address, since_timestamp, count=100, offset=0):
    payload = (
        encode_string(normalize_addr(channel_address))
        + struct.pack("!q", since_timestamp)
        + struct.pack("!q", count)
        + struct.pack("!q", offset)
    )
    return struct.pack("!BH", TYPE_HISTORY, len(payload)) + payload


def get_list_packet(count=100, offset=0):
    payload = struct.pack("!q", count) + struct.pack("!q", offset)
    return struct.pack("!BH", TYPE_LIST, len(payload)) + payload


def sync_history_for_target(target, username, password, since_timestamp=0, count=100, offset=0):
    target = normalize_addr(target)
    if not target:
        return 0

    downloaded = 0

    with create_connection(HOST, PORT) as sock:
        sock.settimeout(5)
        send_handshake(sock)
        send_auth(sock, username, password)
        wait_for_success(sock)
        since_timestamp = max(0, since_timestamp)

        sock.sendall(
            get_history_packet(
                target,
                since_timestamp,
                count=count,
                offset=offset
            )
        )

        sock.settimeout(1.5)
        while True:
            try:
                packet_type, _ = handle_packet(sock)
                if packet_type == TYPE_MESSAGE:
                    downloaded += 1
            except socket.timeout:
                break
            except Exception as exc:
                if str(exc) == "EOF":
                    break
                raise

    return downloaded


def parse_list_item(payload):
    try:
        address, _offset = decode_string(payload, 0)
    except Exception:
        return None

    return normalize_addr(address)


def fetch_available_channels(username, password, count=100, offset=0):
    channels = []

    with create_connection(HOST, PORT) as sock:
        sock.settimeout(5)
        send_handshake(sock)
        send_auth(sock, username, password)
        wait_for_success(sock)
        sock.sendall(get_list_packet(count=count, offset=offset))

        sock.settimeout(1.5)
        while True:
            try:
                packet_type, payload = handle_packet(sock)
                if packet_type == TYPE_LIST:
                    address = parse_list_item(payload)
                    if address:
                        channels.append(address)
            except socket.timeout:
                break
            except Exception as exc:
                if str(exc) == "EOF":
                    break
                raise

    seen = set()
    unique_channels = []
    for address in channels:
        if address in seen:
            continue
        seen.add(address)
        unique_channels.append(address)

    return unique_channels

import hashlib

def make_fingerprint(source, target, content, timestamp):
    raw = f"{source}|{target}|{content}|{int(timestamp.timestamp())}"
    return hashlib.sha256(raw.encode()).hexdigest()

def parse_message(payload):
    offset = 0

    source, offset = decode_string(payload, offset)
    target, offset = decode_string(payload, offset)

    source = normalize_addr(source)
    target = normalize_addr(target)

    timestamp = struct.unpack_from("!Q", payload, offset)[0]
    offset += 8

    content, offset = decode_string(payload, offset)

    # timestamp fix
    if timestamp > 32503680000:
        sekundy = timestamp / 1000.0
    else:
        sekundy = timestamp

    try:
        date_time_field = timezone.datetime.fromtimestamp(
            sekundy,
            tz=timezone.get_current_timezone()
        )
    except Exception:
        date_time_field = timezone.now()

    fp = make_fingerprint(source, target, content, date_time_field)

    obj, created = Message.objects.get_or_create(
        fingerprint=fp,
        defaults={
            "source": source,
            "target": target,
            "timestamp": date_time_field,
            "content": content,
        }
    )

    if created:
        cli(f"received message {source} -> {target} {content}")
    else:
        cli(f"duplicate skipped {source} -> {target}")

def handle_packet(sock):
    header = recv_exact(sock, 3)

    type_payload = header[0]
    length = struct.unpack("!H", header[1:])[0]

    payload = recv_exact(sock, length)

    if type_payload == TYPE_SUCCESS:
        cli("server success packet received")

    elif type_payload == TYPE_ERROR:
        error_code = payload[0]
        cli(f"server error packet received: {error_code}")

    elif type_payload == TYPE_MESSAGE:
        cli("server message packet received")
        parse_message(payload)

    elif type_payload == TYPE_LIST:
        address = parse_list_item(payload)
        if address:
            cli(f"server list item received: {address}")
        else:
            cli("server list item received")

    elif type_payload == TYPE_USERMODE:
        cli("server usermode packet received")

    elif type_payload == TYPE_HISTORY:
        cli("server history packet received")

    elif type_payload == TYPE_HANDSHAKE:
        proto_major = payload[0]
        proto_minor = payload[1]
        cli(f"server handshake packet received: {proto_major}.{proto_minor}")

    else:
        cli(f"UNKNOWN TYPE: {type_payload}")

    return type_payload, payload


def wait_for_success(sock):
    while True:
        packet_type, payload = handle_packet(sock)

        if packet_type == TYPE_SUCCESS:
            return

        if packet_type == TYPE_ERROR:
            error_code = payload[0]
            raise Exception(f"Server rejected request with error {error_code}")


def get_message_packet(source, target, content):
    timestamp = int(time.time())
    source = normalize_addr(source)
    target = normalize_addr(target)
    payload = (
        encode_string(source) +
        encode_string(target) +
        struct.pack("!Q", timestamp) +
        encode_string(content)
    )
    return struct.pack("!BH", TYPE_MESSAGE, len(payload)) + payload


class Command(BaseCommand):
    help = 'Starting new TCP server'

    def handle(self, *args, **options):
        cli("Starting TCP...")
        # keep reconnecting on errors so transient EOFs don't stop the client
        while True:
            try:
                with create_connection(HOST, PORT) as sock:
                    sock.settimeout(None)
                    cli(f"connecting to {HOST}:{PORT} as {AUTH_USER}")
                    send_handshake(sock)
                    send_auth(sock, AUTH_USER, AUTH_PASSWORD)
                    cli("waiting for server success packet")
                   
                    # read packets until connection drops
                    while True:
                        try:
                            handle_packet(sock)
                        except Exception as e:
                            if str(e) == "EOF":
                                cli("server closed connection; reconnecting")
                            else:
                                cli(f"handler error: {e}")
                            break
            except Exception as e:
                cli(f"connect error: {e}")

            # wait a bit before reconnecting
            time.sleep(2)

    