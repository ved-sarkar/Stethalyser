import pyaudio
import serial
import struct

# Setup serial communication (update with your correct port)
ser = serial.Serial('/dev/tty.YOUR_DEVICE', 115200, timeout=1) # Adjust serial port to your setup

# Setup PyAudio for audio playback
p = pyaudio.PyAudio()

# Open an audio stream with 16-bit format, 1 channel, and 8000 Hz sample rate
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=8000,  # 8000 Hz sample rate for basic audio quality
                output=True)

# Main loop to read from serial and output audio
while True:
    # Read 2 bytes from the serial port (representing one 16-bit sample)
    data = ser.read(2)
    
    if len(data) == 2:
        # Unpack the two bytes into a signed 16-bit integer
        audio_sample = struct.unpack('<h', data)[0]
        
        # Play the sound by writing it to the audio stream
        stream.write(struct.pack('<h', audio_sample))

# Clean up when done
stream.stop_stream()
stream.close()
p.terminate()
