import struct
import time


SERVER_DOMAIN = "rctt.net"

TYPE_SUCCESS = 0x01
TYPE_ERROR = 0x02
TYPE_HANDSHAKE = 0x03
TYPE_AUTH = 0x04
TYPE_MESSAGE = 0x05
TYPE_LIST = 0x06
TYPE_USERMODE = 0x07
TYPE_HISTORY = 0x08


def encode_string(s):
    encoded = s.encode("utf-8")
    return struct.pack("!H", len(encoded)) + encoded


def decode_string(payload, offset):
    length = struct.unpack_from("!H", payload, offset)[0]
    offset += 2
    text = payload[offset : offset + length].decode("utf-8")
    return text, offset + length


def _normalize_address(address):
    address = (address or "").strip()
    if not address:
        return address

    if "@" not in address:
        return f"{address}@{SERVER_DOMAIN}"

    user, _host = address.split("@", 1)
    return f"{user}@{SERVER_DOMAIN}"


def get_handshake():
    payload = struct.pack("!BBB", 0, 1, 1)
    return struct.pack("!BH", TYPE_HANDSHAKE, len(payload)) + payload


def get_auth(user, password):
    payload = encode_string(user) + encode_string(password)
    return struct.pack("!BH", TYPE_AUTH, len(payload)) + payload


def get_join_channel(my_username, target_channel):
    clean_user = _normalize_address(my_username)
    clean_room = (target_channel or "").strip()
    if not clean_room.startswith("#"):
        clean_room = f"#{clean_room}"
    clean_room = _normalize_address(clean_room)

    payload = (
        encode_string(clean_user)
        + encode_string(clean_room)
        + struct.pack("!B", 0x01)
    )
    return struct.pack("!BH", TYPE_USERMODE, len(payload)) + payload


def get_leave_channel(my_username, target_channel):
    clean_user = _normalize_address(my_username)
    clean_room = (target_channel or "").strip()
    if not clean_room.startswith("#"):
        clean_room = f"#{clean_room}"
    clean_room = _normalize_address(clean_room)

    payload = (
        encode_string(clean_user)
        + encode_string(clean_room)
        + struct.pack("!B", 0x00)
    )
    return struct.pack("!BH", TYPE_USERMODE, len(payload)) + payload


def get_list_packet(count=100, offset=0):
    payload = struct.pack("!q", count) + struct.pack("!q", offset)
    return struct.pack("!BH", TYPE_LIST, len(payload)) + payload


def get_message_packet(source, target, content):
    timestamp = int(time.time())
    payload = (
        encode_string(_normalize_address(source))
        + encode_string(_normalize_address(target))
        + struct.pack("!Q", timestamp)
        + encode_string(content)
    )
    return struct.pack("!BH", TYPE_MESSAGE, len(payload)) + payload


def parse_message(payload):
    offset = 0
    try:
        source, offset = decode_string(payload, offset)
        target, offset = decode_string(payload, offset)
        timestamp = struct.unpack_from("!Q", payload, offset)[0]
        offset += 8
        content, _ = decode_string(payload, offset)

        return {
            "source": _normalize_address(source),
            "target": _normalize_address(target),
            "timestamp": timestamp,
            "content": content,
        }
    except Exception:
        return None


def get_usermode_packet(user_address, channel_name, mode=0x01):
    payload = (
        encode_string(_normalize_address(user_address))
        + encode_string(_normalize_address(channel_name))
        + struct.pack("!B", mode)
    )
    return struct.pack("!BH", TYPE_USERMODE, len(payload)) + payload


def get_history_packet(channel_address, since_timestamp, count=100, offset=0):
    payload = (
        encode_string(_normalize_address(channel_address))
        + struct.pack("!q", since_timestamp)
        + struct.pack("!q", count)
        + struct.pack("!q", offset)
    )
    return struct.pack("!BH", TYPE_HISTORY, len(payload)) + payload
  