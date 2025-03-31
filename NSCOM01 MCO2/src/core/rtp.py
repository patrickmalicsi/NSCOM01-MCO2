import struct
from typing import Tuple

class RTPPacket:
    """RTP packet structure according to RFC 3550"""
    
    def __init__(self):
        self.version = 2
        self.padding = 0
        self.extension = 0
        self.cc = 0
        self.marker = 0
        self.payload_type = 0  # PCMU
        self.sequence_number = 0
        self.timestamp = 0
        self.ssrc = 0
        self.payload = b''

    def pack(self) -> bytes:
        """Packs RTP header and payload into binary"""
        header = struct.pack(
            '!BBHII',
            (self.version << 6) | (self.padding << 5) | (self.extension << 4) | self.cc,
            (self.marker << 7) | self.payload_type,
            self.sequence_number,
            self.timestamp,
            self.ssrc
        )
        return header + self.payload

    def unpack(self, data: bytes):
        """Unpacks binary RTP packet"""
        header = struct.unpack('!BBHII', data[:12])
        self.version = header[0] >> 6
        self.payload_type = header[1] & 0x7F
        self.sequence_number = header[2]
        self.timestamp = header[3]
        self.ssrc = header[4]
        self.payload = data[12:]