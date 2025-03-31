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
        self.rtp_socket.bind(('0.0.0.0', rtp_port))
        self.ssrc = ssrc
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.active = False
        self.lock = threading.Lock()

    def stream_from_file(self, filename: str, remote_ip: str, remote_port: int):
        """Streams audio from WAV file via RTP"""
        try:
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
                
                self.rtp_socket.sendto(packet.pack(), (remote_ip, remote_port))
                data = wf.readframes(chunk_size)
                time.sleep(0.02)  # Maintain 50 packets/sec
        except Exception as e:
            print(f"Error during audio streaming: {e}")
        finally:
            wf.close()

    def play_stream(self):
        """Receives and plays RTP audio stream"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=8000,
                output=True
            )
            self.active = True
            
            while self.active:
                data, _ = self.rtp_socket.recvfrom(2048)
                if not data:
                    continue
                packet = RTPPacket()
                packet.unpack(data)
                if packet.payload:
                    self.stream.write(packet.payload)
        except Exception as e:
            print(f"Error during audio playback: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()

    def stop(self):
        """Cleanup audio resources"""
        with self.lock:
            self.active = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        self.rtp_socket.close()