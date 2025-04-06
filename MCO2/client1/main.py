from sip_client import SIPClient
from rtp_sender import RTPSender

def main():
    # Use localhost for testing
    sip_client = SIPClient(local_ip="127.0.0.1", local_port=5060, remote_ip="127.0.0.1", remote_port=5061)
    rtp_sender = RTPSender(audio_file="audio.wav", remote_ip="127.0.0.1", remote_port=5004)

    try:
        # Start SIP call
        print("Starting SIP call...")
        sip_client.start_call()
        print("SIP call established.")

        # Send RTP audio
        print("Sending RTP audio...")
        rtp_sender.send_audio()
        print("RTP audio transmission complete.")

    except FileNotFoundError:
        print("Error: Audio file 'audio.wav' not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # End SIP call
        print("Ending SIP call...")
        sip_client.end_call()
        print("SIP call terminated.")

if __name__ == "__main__":
    main()