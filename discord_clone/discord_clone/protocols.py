import socket
import struct


HOST = "127.0.0.1"
PORT = 9999

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def get_data_type_and_length(client , length):
    data = b''
    #until data  < length
    while len(data) < length:
        #chunk = 3 - 0 
        chunk = client.recv(length-len(data))
        if not chunk:
            raise Exception("EOF")
        data += chunk
    return data


def send_handshake():
    hanshake = struct.pack("!BHBB", 3, 2, 0, 1)
    client.sendall(hanshake)

def encode_string(s:str):
    phrase = s.encode("utf-8")
    return struct.pack("!H", len(phrase)) + phrase
 
#auth
def send_auth():
    login = encode_string("kacper")
    password = encode_string("valid")

    auth_login = login + password
    
    auth = struct.pack("!BH", 4, len(auth_login) ) + auth_login
    client.sendall(auth)

def recive_type(sock):
    header = get_data_type_and_length(sock, 3)
    type_payload = header[0]
    length = struct.unpack("!H", header[1:])[0]
    
    payload = get_data_type_and_length(s, length)

    offset = 0

    #source 2 bajty
    length = int.from_bytes(payload[offset:offset+2], "big")
    offset +=2
    source = payload[offset:offset+length].decode()
    offset+= length 

    # target 2 bajty
    length = int.from_bytes(payload[offset:offset+2], 'big')
    offset += 2
    target = payload[offset:offset+length].decode()
    offset += length

    # timestamp 8 bajtow
    length = int.from_bytes(payload[offset:offset+8], "big")
    offset += 8
    timestamp = payload[offset]
    offset += 2

    # content to the end
    content = payload[offset:].decode(errors='ignore')
    print(source, target, timestamp, content)

    print(f"Source -> {source}, to: {target}, message: {content}")

with client as s:
    try:
        s.connect((HOST, PORT))

        #we want to recive 3 bytes to read type and payload length
        header = get_data_type_and_length(s, 3)
        type_payload = header[0]
        length = struct.unpack("!H", header[1:])[0]

        payload = get_data_type_and_length(s, length)

        print("get handshake")
        send_handshake()
        print("handshake sent")
        send_auth()
        print("auth correct")
        while True:
            
           recive_type(s)

     
    except Exception as exc:
        print(f"Exception: {exc}")
  