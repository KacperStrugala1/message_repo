from time import sleep
import struct
import socket

HOST="0.0.0.0"
PORT=9999

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.connect((HOST, PORT))


#> - big endian 
#0x01-00000001	Handshake version = 1

# #0x02-00000010	Ping
ping = struct.pack(">B", 0x02)
packet_type = serversocket.recv(1)
print(f"{packet_type}")

while True:
    
    #ping i pong
    #recive 1 byte
    packet_type = serversocket.recv(1)
    sleep(3)
    serversocket.sendall(ping)
    if packet_type == b"\x03":
        #uint64 -8 bytes so read 8 bytes
        pong = serversocket.recv(8)
        #unpack bytes stream
        timestamp = struct.unpack(">Q", pong)[0]
        print(f"Timestamp : {timestamp}")
    #     #0xFF-00000010	Test
        
    #     serversocket.sendall(ping)

    elif packet_type == b"\x04":  # Message
            data = bytearray()

            while True:
                b = serversocket.recv(1)
                if b == b'\x00':
                    break
                data += b

            text = data.decode("utf-8")
            print("Message:", text)
