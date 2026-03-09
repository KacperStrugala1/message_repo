class Packet:

    def __init__(self, payload_type, payload_length, payload):
        self.payload_type = payload_type
        self.payload_length = payload_length
        self.payload = payload
