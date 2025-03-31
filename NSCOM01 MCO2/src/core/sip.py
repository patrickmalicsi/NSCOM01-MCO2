import socket
import time
import struct
from typing import Tuple, Optional

class SIPClient:
    def __init__(self, local_ip: str, local_port: int):
        self.local_ip = local_ip
        self.local_port = local_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((local_ip, local_port))

    def send_invite(self, remote_ip: str, remote_port: int, rtp_port: int) -> str:
        """Sends SIP INVITE with SDP offer"""
        sdp = self._generate_sdp(rtp_port)
        invite = (
            f"INVITE sip:{remote_ip}:{remote_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
            f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
            f"To: <sip:{remote_ip}:{remote_port}>\r\n"
            f"Call-ID: {int(time.time())}@{self.local_ip}\r\n"
            f"CSeq: 1 INVITE\r\n"
            f"Content-Type: application/sdp\r\n"
            f"Content-Length: {len(sdp)}\r\n\r\n"
            f"{sdp}"
        )
        self.socket.sendto(invite.encode(), (remote_ip, remote_port))
        return invite

    def _generate_sdp(self, rtp_port: int) -> str:
        """Generates SDP body for SIP messages"""
        return (
            "v=0\r\n"
            f"o=- {int(time.time())} {int(time.time())} IN IP4 {self.local_ip}\r\n"
            "s=VoIP Call\r\n"
            f"c=IN IP4 {self.local_ip}\r\n"
            "t=0 0\r\n"
            f"m=audio {rtp_port} RTP/AVP 0\r\n"  # PCMU payload type 0
            "a=rtpmap:0 PCMU/8000\r\n"
        )

    def wait_for_response(self, timeout: int = 5) -> Tuple[Optional[int], Optional[str]]:
        """Waits for SIP response and parses SDP answer"""
        self.socket.settimeout(timeout)
        try:
            data, addr = self.socket.recvfrom(2048)
            if b"SIP/2.0 200 OK" in data:
                return self._parse_sdp(data.decode()), None
            elif b"SIP/2.0" in data:  # Any error response
                return None, data.decode()
        except socket.timeout:
            return None, "Timeout waiting for response"

    def _parse_sdp(self, message: str) -> int:
        """Extracts RTP port from SDP answer"""
        for line in message.split('\r\n'):
            if line.startswith('m=audio'):
                return int(line.split(' ')[1])
        raise ValueError("No audio media in SDP")

    def send_ack(self, remote_ip: str, remote_port: int):
        """Sends SIP ACK"""
        ack = (
            f"ACK sip:{remote_ip}:{remote_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
            f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
            f"To: <sip:{remote_ip}:{remote_port}>\r\n"
            f"Call-ID: {int(time.time())}@{self.local_ip}\r\n"
            f"CSeq: 1 ACK\r\n\r\n"
        )
        self.socket.sendto(ack.encode(), (remote_ip, remote_port))

    def send_bye(self, remote_ip: str, remote_port: int):
        """Sends SIP BYE to terminate call"""
        bye = (
            f"BYE sip:{remote_ip}:{remote_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
            f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
            f"To: <sip:{remote_ip}:{remote_port}>\r\n"
            f"Call-ID: {int(time.time())}@{self.local_ip}\r\n"
            f"CSeq: 2 BYE\r\n\r\n"
        )
        self.socket.sendto(bye.encode(), (remote_ip, remote_port))