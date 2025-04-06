from sip_client import SIPClient
from rtp_receiver import RTPReceiver

def main():
    # Use localhost for testing
    sip_client = SIPClient(local_ip="127.0.0.1", local_port=5061, remote_ip="127.0.0.1", remote_port=5060)
    rtp_receiver = RTPReceiver(local_port=5004)

    try:
        # Receive SIP call
        print("Waiting for SIP INVITE...")
        sip_client.receive_call()
        print("SIP call established.")

        # Receive RTP audio
        print("Receiving RTP audio...")
        rtp_receiver.receive_audio()
        print("RTP audio reception complete.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # End SIP call
        print("Ending SIP call...")
        sip_client.end_call()
        print("SIP call terminated.")

if __name__ == "__main__":
    main()