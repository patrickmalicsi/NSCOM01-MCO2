import argparse
import json
import threading
from core.sip import SIPClient
from audio.streamer import AudioStreamer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True, help='Path to config file')
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    # Initialize components
    sip = SIPClient(config['local_ip'], config['sip_port'])
    audio = AudioStreamer(config['rtp_port'], config['rtcp_port'])

    try:
        if config.get('initiator', False):
            # Caller logic
            print(f"Calling {config['remote_ip']}:{config['remote_sip_port']}")
            try:
                sip.send_invite(config['remote_ip'], config['remote_sip_port'], config['rtp_port'])
                remote_rtp_port, error = sip.wait_for_response(timeout=10)
                if error:
                    print(f"Call failed: {error}")
                    return
                sip.send_ack(config['remote_ip'], config['remote_sip_port'])
            except Exception as e:
                print(f"Error during call setup: {e}")
                return

            # Start audio in separate thread
            audio_thread = threading.Thread(
                target=audio.stream_from_file,
                args=(config.get('audio_file', 'samples/audio/test.wav'), config['remote_ip'], remote_rtp_port)
            )
            audio_thread.start()

        else:
            # Callee logic
            print("Waiting for incoming call...")
            while True:
                received_message, error = sip.wait_for_response(timeout=30)
                if error:
                    print(f"Failed to receive call: {error}")
                    return

                print("Received SIP message:")
                print(received_message)  # Print the raw SIP message

                # Handle BYE message
                if "BYE" in received_message:
                    print("Call terminated by remote host.")
                    return

                # Parse the SIP INVITE to extract the RTP port
                if "m=audio" in received_message:
                    lines = received_message.split("\n")
                    for line in lines:
                        if line.startswith("m=audio"):
                            remote_rtp_port = int(line.split()[1])  # Extract the RTP port
                            print(f"Extracted RTP port: {remote_rtp_port}")
                            break
                else:
                    print("No audio information found in the SIP message.")
                    return

                # Send 200 OK response to the caller
                print("Incoming call received. Sending 200 OK...")
                sip.send_ok(config['remote_ip'], config['remote_sip_port'], config['rtp_port'])

                # Start audio playback in a separate thread
                try:
                    audio_thread = threading.Thread(
                        target=audio.play_stream  # No arguments passed
                    )
                    audio_thread.start()
                except Exception as e:
                    print(f"Error during audio playback: {e}")
                    return

                # Wait for user input to terminate the call
                input("Press Enter to end call...")
                sip.send_bye(config['remote_ip'], config['remote_sip_port'])
                return

    finally:
        audio.stop()
        if config.get('initiator', False):
            sip.send_bye(config['remote_ip'], config['remote_sip_port'])
        if 'audio_thread' in locals() and audio_thread.is_alive():
            audio_thread.join()

if __name__ == "__main__":
    main()