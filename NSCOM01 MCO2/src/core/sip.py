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
        self.call_id = f"{int(time.time())}@{self.local_ip}"  # Generate a consistent Call-ID

    def send_invite(self, remote_ip: str, remote_port: int, rtp_port: int) -> str:
        """Sends SIP INVITE with SDP offer"""
        sdp = self._generate_sdp(rtp_port)
        invite = (
            f"INVITE sip:{remote_ip}:{remote_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
            f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
            f"To: <sip:{remote_ip}:{remote_port}>\r\n"
            f"Call-ID: {self.call_id}\r\n"
            "CSeq: 1 INVITE\r\n"
            "Content-Type: application/sdp\r\n"
            f"Content-Length: {len(sdp)}\r\n\r\n"
            f"{sdp}"
        )
        self.socket.sendto(invite.encode(), (remote_ip, remote_port))
        print(f"Sent INVITE to {remote_ip}:{remote_port}")
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

    def wait_for_response(self, timeout: int = 5) -> Tuple[Optional[str], Optional[str]]:
        """Waits for SIP response and parses SDP answer"""
        self.socket.settimeout(timeout)
        try:
            data, addr = self.socket.recvfrom(2048)
            message = data.decode()
            print(f"Received SIP message:\n{message}")

            # Check for specific SIP responses
            if "SIP/2.0 200 OK" in message:
                print("SIP 200 OK received.")
                return message, None
            elif "SIP/2.0 4" in message:  # Handle 4xx errors
                print("SIP error response received.")
                return None, message
            elif "INVITE" in message:
                print("SIP INVITE received.")
                return message, None
            else:
                print("Unknown SIP response received.")
                return None, "Unknown SIP response received"

        except socket.timeout:
            return None, "Timeout waiting for response"
        except Exception as e:
            return None, f"Error while waiting for SIP response: {e}"

    def _parse_sdp(self, message: str) -> int:
        """Extracts RTP port from SDP answer"""
        if "Content-Type: application/sdp" not in message:
            raise ValueError("No SDP content in SIP response")

        for line in message.split('\r\n'):
            if line.startswith('m=audio'):
                try:
                    rtp_port = int(line.split(' ')[1])  # Extract the RTP port
                    print(f"Extracted RTP port from SDP: {rtp_port}")
                    return rtp_port
                except (IndexError, ValueError):
                    raise ValueError("Malformed SDP media line: " + line)
        raise ValueError("No audio media line found in SDP")

    def send_ack(self, remote_ip: str, remote_port: int):
        """Sends SIP ACK"""
        ack = (
            f"ACK sip:{remote_ip}:{remote_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
            f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
            f"To: <sip:{remote_ip}:{remote_port}>\r\n"
            f"Call-ID: {self.call_id}\r\n"
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
            f"Call-ID: {self.call_id}\r\n"
            f"CSeq: 2 BYE\r\n\r\n"
        )
        self.socket.sendto(bye.encode(), (remote_ip, remote_port))

    def send_ok(self, remote_ip: str, remote_port: int, rtp_port: int):
        """Sends SIP 200 OK with SDP answer"""
        sdp = self._generate_sdp(rtp_port)
        response = (
            "SIP/2.0 200 OK\r\n"
            f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
            f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
            f"To: <sip:{remote_ip}:{remote_port}>\r\n"
            f"Call-ID: {self.call_id}\r\n"
            "CSeq: 1 INVITE\r\n"
            "Content-Type: application/sdp\r\n"
            f"Content-Length: {len(sdp)}\r\n\r\n"
            f"{sdp}"
        )
        self.socket.sendto(response.encode(), (remote_ip, remote_port))
        print(f"Sent 200 OK to {remote_ip}:{remote_port}")