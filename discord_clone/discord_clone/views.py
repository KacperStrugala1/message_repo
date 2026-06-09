from django.http import HttpResponse
from django.views import View
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.utils import timezone
import time
from .utils import socket_connect as sc
from .models import Message
from . import protocols
import socket

from .management.commands.tcp_client import (
    AUTH_PASSWORD,
    AUTH_USER,
    HOST,
    PORT,
    create_connection,
    send_auth,
    send_handshake,
    send_message,
    fetch_available_channels,
    sync_history_for_target,
    wait_for_success,
)


USER_DOMAIN = "rctt.net"
DEFAULT_USERNAME = f"kacper@{USER_DOMAIN}"
DEFAULT_PASSWORD = "SnKpJmnSgkwW"
DEFAULT_CHANNELS = ("#tel", "#test")
ALLOWED_CHANNEL_LABELS = {"#tel", "#test"}
ALLOWED_USER_LABELS = {"damian", "kuba", "bt", "ks"}


def last_message_timestamp(target):
    from django.db.models import Max, Q

    last_timestamp = Message.objects.filter(Q(target=target) | Q(source=target)).aggregate(last=Max("timestamp"))["last"]
    if not last_timestamp:
        return 0
    return int(last_timestamp.timestamp())


def sync_chat_history(target, username, password):
    if not target:
        return

    try:
        since_timestamp = last_message_timestamp(target)
        sync_history_for_target(target, AUTH_USER, AUTH_PASSWORD, since_timestamp=since_timestamp, count=100, offset=0)
    except Exception as exc:
        print(f"Błąd pobierania historii dla {target}: {exc}")


def sync_available_channels(username, password, count=100, offset=0):
    try:
        return fetch_available_channels(AUTH_USER, AUTH_PASSWORD, count=count, offset=offset)
    except Exception as exc:
        print(f"Błąd pobierania listy kanałów: {exc}")
        return []


def channel_addr(name):
    name = (name or "").strip()
    if not name.startswith("#"):
        name = f"#{name}"
    if "@" in name:
        return user_addr(name)
    return f"{name}@{USER_DOMAIN}"


def user_addr(username):
    username = (username or "").strip()
    if not username:
        return DEFAULT_USERNAME
    if "@" in username:
        user, _host = username.split("@", 1)
        return f"{user}@{USER_DOMAIN}"
    return f"{username}@{USER_DOMAIN}"


def normalize_addr(addr):
    try:
        user, _host = addr.split("@", 1)
    except Exception:
        return addr

    return f"{user}@{USER_DOMAIN}"


def is_allowed_sidebar_address(addr):
    normalized = normalize_addr(addr)
    if normalized.startswith("#"):
        return normalized.split("@", 1)[0] in ALLOWED_CHANNEL_LABELS

    label = normalized.split("@", 1)[0]
    return label in ALLOWED_USER_LABELS


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
        username = request.POST.get("username", "").strip() or DEFAULT_USERNAME
        password = request.POST.get("password", "").strip() or DEFAULT_PASSWORD
        request.session["username"] = user_addr(username)
        request.session["password"] = password
        return redirect("channel_view")


class ChannelView(View):
    template_name = "channel.html"

    
    def get(self, request):
        # derive available channels from messages and the server-side List packet
        all_addresses = set()
        for m in Message.objects.all().values_list("source", "target"):
            all_addresses.update([a for a in m if a and "@" in a and is_allowed_sidebar_address(a)])

        list_count_raw = request.GET.get("count", "100")
        list_offset_raw = request.GET.get("offset", "0")
        try:
            list_count = int(list_count_raw)
        except ValueError:
            list_count = 100
        try:
            list_offset = int(list_offset_raw)
        except ValueError:
            list_offset = 0

        all_addresses.update(
            sync_available_channels(
                request.session.get("username", DEFAULT_USERNAME),
                request.session.get("password", DEFAULT_PASSWORD),
                count=list_count,
                offset=list_offset,
            )
        )

        # produce list of channel objects with label (user part) and addr (full address)
        channels = []
        seen = set()
        for raw_addr in sorted(all_addresses):
            addr = normalize_addr(raw_addr)
            if not is_allowed_sidebar_address(addr):
                continue
            if addr in seen:
                continue
            seen.add(addr)

            label = addr.split('@', 1)[0]
            # skip anonymous or empty labels
            if not label or label.lower() == "anonymous":
                continue
            channels.append({"addr": addr, "label": label})

        # ensure default channels always exist in the sidebar
        for ch in DEFAULT_CHANNELS:
            addr = channel_addr(ch)
            if not any(c["addr"] == addr for c in channels):
                channels.append({"addr": addr, "label": ch})

        # choose target: GET param or first available channel
        target = request.GET.get("target")
        # normalize requested target
        if target:
            target = normalize_addr(target)

        if not target:
            target = channel_addr("#tel")

        sync_chat_history(target, request.session.get("username", DEFAULT_USERNAME), request.session.get("password", DEFAULT_PASSWORD))

        # show both messages sent to and sent from this address so the conversation is readable
        if target:
            from django.db.models import Q
            messages = list(Message.objects.filter(Q(target=target) | Q(source=target)).order_by("id")[:30])
        else:
            messages = []
        current_username = user_addr(request.session.get("username", DEFAULT_USERNAME))
        last_message_id = messages[-1].id if messages else 0

        return render(request, self.template_name, {
            "messages": messages,
            "current_target": target,
            "current_username": current_username,
            "channels": channels,
            "last_message_id": last_message_id,
        })
    
class ApiView(View):
    def get(self, request):
        target = request.GET.get("target")
        # normalize target to match stored addresses
        def normalize_addr(addr):
            try:
                user, host = addr.split("@", 1)
            except Exception:
                return addr

            return f"{user}@{USER_DOMAIN}"

        if target:
            target = normalize_addr(target)
        if not target:
            return JsonResponse({"messages": []})

        since_id_raw = request.GET.get("since_id", "0")
        try:
            since_id = int(since_id_raw)
        except ValueError:
            since_id = 0

        if request.GET.get("sync") == "1":
            sync_chat_history(target, request.session.get("username", DEFAULT_USERNAME), request.session.get("password", DEFAULT_PASSWORD))

        from django.db.models import Q
        messages = (
            Message.objects.filter(Q(target=target) | Q(source=target), id__gt=since_id)
            .order_by("id")
            .values("id", "source", "target", "content", "timestamp")[:30]
        )

        messages_data = []
        for message in messages:
            messages_data.append({
                "id": message["id"],
                "source": message["source"],
                "target": message["target"],
                "content": message["content"],
                "timestamp": message["timestamp"].isoformat(),
            })

        return JsonResponse({"messages": messages_data})

    def post(self, request):
        content = request.POST.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Message content is required."}, status=400)

        username = request.session.get("username") or request.POST.get("source", "").strip() or DEFAULT_USERNAME
        password = request.session.get("password", DEFAULT_PASSWORD)
        channel_name = request.POST.get("target", "").strip() or ""

        def normalize_addr(addr):
            try:
                user, host = addr.split("@", 1)
            except Exception:
                return addr

            return f"{user}@{USER_DOMAIN}"

        source = normalize_addr(user_addr(username))
        target = normalize_addr(channel_name)
        message_timestamp = int(time.time())
        message_datetime = timezone.datetime.fromtimestamp(
            message_timestamp,
            tz=timezone.get_current_timezone(),
        )

        try:
            with create_connection(HOST, PORT) as sock:
                sock.settimeout(5)
                send_handshake(sock)
                send_auth(sock, AUTH_USER, AUTH_PASSWORD)
                wait_for_success(sock)
                send_message(sock, source, target, content, timestamp=message_timestamp)
        except Exception as exc:
            print(f"Błąd wysyłania wiadomości do serwera dla {target}: {exc}")
            # fallback: save message locally so offline/test channels still work
            message = Message.objects.create(
                source=source,
                target=target,
                timestamp=message_datetime,
                content=content,
            )

            return JsonResponse({
                "status": "saved_local",
                "message": {
                    "source": message.source,
                    "target": message.target,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                },
            }, status=201)

        # if we reached here, the message was sent to the TCP server successfully.
        # Persist a local copy so the UI can reflect the outgoing message immediately
        message = Message.objects.create(
            source=source,
            target=target,
            timestamp=message_datetime,
            content=content,
        )

        return JsonResponse({
            "status": "sent",
            "message": {
                "id": message.id,
                "source": message.source,
                "target": message.target,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            },
        }, status=202)


class AddTestChannelView(View):
    """Create a lightweight test channel by inserting a short message for the given username."""

    def post(self, request):
        username = request.POST.get("username", "").strip()
        if not username:
            return JsonResponse({"error": "username is required"}, status=400)

        addr = user_addr(username)
        message = Message.objects.create(
            source=addr,
            target=addr,
            timestamp=timezone.now(),
            content="(test channel created)",
        )

        return JsonResponse({
            "status": "created",
            "channel": addr,
            "message": {
                "source": message.source,
                "target": message.target,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            },
        }, status=201)
