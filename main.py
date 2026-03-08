import socket
import struct

HOST="127.0.0.1"
PORT=9999

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.connect((HOST, PORT))

#> - big endian 
#0x01-00000001	Handshake version = 1
version = 2
handshake = struct.pack(">BB", 0x01, version)
serversocket.sendall(handshake)
#0x02-00000010	Ping
ping = struct.pack(">B", 0x02)
serversocket.sendall(ping)
#0x03-00000011	Pong
pong = struct.pack(">B", 0x03)
#0x04-00000100	Message
pong = struct.pack(">B", 0x04)
#0xFF-00000010	Test

