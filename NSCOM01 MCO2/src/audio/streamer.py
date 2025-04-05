import socket
import time
import wave
import pyaudio
import threading
from typing import Optional
from core.rtp import RTPPacket

class AudioStreamer:
    def __init__(self, rtp_port: int, rtcp_port: int, ssrc: int = 12345678):
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp_socket.bind(('0.0.0.0', rtp_port))  # Bind to the RTP port
        self.ssrc = ssrc
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.active = False
        self.lock = threading.Lock()

    def stream_from_file(self, filename: str, remote_ip: str, remote_port: int):
        """Streams audio from WAV file via RTP"""
        try:
            print(f"Starting audio streaming from file: {filename}")
            wf = wave.open(filename, 'rb')
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 8000:
                raise ValueError("WAV file must be mono, 16-bit, 8000 Hz")
            
            packet = RTPPacket()
            packet.ssrc = self.ssrc
            
            # Send 20ms chunks (160 samples for 8000Hz)
            chunk_size = 160
            data = wf.readframes(chunk_size)
            
            while data and self.active:
                packet.payload = data
                packet.sequence_number += 1
                packet.timestamp += chunk_size
                
                print(f"Sending RTP packet: sequence_number={packet.sequence_number}, timestamp={packet.timestamp}")
                self.rtp_socket.sendto(packet.pack(), (remote_ip, remote_port))
                data = wf.readframes(chunk_size)
                time.sleep(0.02)  # Maintain 50 packets/sec
            print("Audio streaming completed.")
        except Exception as e:
            print(f"Error during audio streaming: {e}")
        finally:
            wf.close()

    def play_stream(self):
        # """Receives and plays RTP audio stream"""
        try:
            print("Starting audio playback...")
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=8000,
                output=True
            )
            self.active = True
            
            while self.active:
                try:
                    if self.rtp_socket.fileno() == -1:  # Check if the socket is closed
                        print("RTP socket is closed. Stopping playback.")
                        break
                    data, _ = self.rtp_socket.recvfrom(2048)  # Receive RTP packets
                    if not data:
                        continue
                    packet = RTPPacket()
                    packet.unpack(data)  # Unpack the RTP packet
                    if packet.payload:
                        print(f"Received RTP packet: sequence_number={packet.sequence_number}, timestamp={packet.timestamp}")
                        self.stream.write(packet.payload)  # Play the audio payload
                except Exception as e:
                    print(f"Error receiving RTP packet: {e}")
                    break
            print("Audio playback stopped.")
        except Exception as e:
            print(f"Error during audio playback: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()

    def stop(self):
        """Cleanup audio resources"""
        print("Stopping audio streamer...")
        with self.lock:
            self.active = False  # Stop the playback loop
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        if self.rtp_socket.fileno() != -1:  # Check if the socket is still open
            print(f"Stopping RTP socket: {self.rtp_socket.fileno()}")
            self.rtp_socket.close()
        print("Audio streamer stopped.")