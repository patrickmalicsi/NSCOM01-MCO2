import socket
import uuid

class SIPClient:
    def __init__(self, local_ip, local_port, remote_ip, remote_port):
        self.local_ip = local_ip
        self.local_port = local_port
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.local_ip, self.local_port))
        self.call_id = str(uuid.uuid4())  # Generate a unique Call-ID

    def start_call(self):
        # SDP Body
        sdp_body = f"v=0\r\n"
        sdp_body += f"o=- 0 0 IN IP4 {self.local_ip}\r\n"
        sdp_body += f"s=VoIP Call\r\n"
        sdp_body += f"c=IN IP4 {self.local_ip}\r\n"
        sdp_body += f"t=0 0\r\n"
        sdp_body += f"m=audio {self.local_port} RTP/AVP 0\r\n"
        sdp_body += f"a=rtpmap:0 PCMU/8000\r\n"

        # INVITE Message
        invite_message = f"INVITE sip:{self.remote_ip}:{self.remote_port} SIP/2.0\r\n"
        invite_message += f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
        invite_message += f"To: <sip:{self.remote_ip}:{self.remote_port}>\r\n"
        invite_message += f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
        invite_message += f"Call-ID: {self.call_id}\r\n"
        invite_message += "CSeq: 1 INVITE\r\n"
        invite_message += "Content-Type: application/sdp\r\n"
        invite_message += f"Content-Length: {len(sdp_body)}\r\n\r\n"
        invite_message += sdp_body
        self.sock.sendto(invite_message.encode(), (self.remote_ip, self.remote_port))

        # Wait for 200 OK
        try:
            response, _ = self.sock.recvfrom(1024)
            if b"200 OK" in response:
                # ACK Message
                ack_message = f"ACK sip:{self.remote_ip}:{self.remote_port} SIP/2.0\r\n"
                ack_message += f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
                ack_message += f"To: <sip:{self.remote_ip}:{self.remote_port}>\r\n"
                ack_message += f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
                ack_message += f"Call-ID: {self.call_id}\r\n"
                ack_message += "CSeq: 1 ACK\r\n"
                ack_message += "Content-Length: 0\r\n\r\n"
                self.sock.sendto(ack_message.encode(), (self.remote_ip, self.remote_port))
            else:
                print("Error: Did not receive 200 OK.")
        except socket.timeout:
            print("Error: Timeout waiting for 200 OK.")
        except Exception as e:
            print(f"Error: {e}")

    def end_call(self):
        # BYE Message
        bye_message = f"BYE sip:{self.remote_ip}:{self.remote_port} SIP/2.0\r\n"
        bye_message += f"Via: SIP/2.0/UDP {self.local_ip}:{self.local_port}\r\n"
        bye_message += f"To: <sip:{self.remote_ip}:{self.remote_port}>\r\n"
        bye_message += f"From: <sip:{self.local_ip}:{self.local_port}>\r\n"
        bye_message += f"Call-ID: {self.call_id}\r\n"
        bye_message += "CSeq: 2 BYE\r\n"
        bye_message += "Content-Length: 0\r\n\r\n"
        self.sock.sendto(bye_message.encode(), (self.remote_ip, self.remote_port))
        self.sock.close()