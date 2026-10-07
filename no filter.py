import serial
import numpy as np
import wave
import time
import traceback
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import threading

# Configure settings
SERIAL_PORT = '/dev/tty.YOUR_DEVICE'
BAUD_RATE = 115200
ARDUINO_SAMPLE_RATE = 44100  # Original Arduino sampling rate
AUDIO_SAMPLE_RATE = 44100  # Standard audio sample rate
RECORD_DURATION = 10  # Recording duration in seconds
FILENAME = "stethoscope_recording.wav"
PLOT_LENGTH = 1000  # Number of points to display

# Initialize plot
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(12, 6))
line, = ax.plot([], [], 'g-', linewidth=1)
ax.set_ylim(-1, 1)
ax.set_xlim(0, PLOT_LENGTH)
ax.set_title('Real-time Stethoscope Audio Waveform')
ax.set_xlabel('Samples')
ax.set_ylabel('Amplitude')
ax.grid(True)

# Create deque for plotting
plot_data = deque(maxlen=PLOT_LENGTH)
plot_data.extend([0] * PLOT_LENGTH)

def connect_to_arduino(port, baud_rate, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            print(f"Attempting to connect to Arduino (attempt {attempt + 1}/{max_attempts})...")
            try:
                arduino = serial.Serial()
                arduino.port = port
                if arduino.is_open:
                    arduino.close()
            except:
                pass
            
            arduino = serial.Serial(port, baud_rate, timeout=1)
            time.sleep(2)  # Add delay for Arduino reset
            print("Successfully connected to Arduino!")
            return arduino
        except serial.SerialException as e:
            print(f"Connection attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2)
    
    raise Exception("Could not connect to Arduino after multiple attempts")

def update_plot(frame):
    line.set_data(range(PLOT_LENGTH), list(plot_data))
    return line,

def record_audio():
    try:
        # Connect to Arduino
        arduino = connect_to_arduino(SERIAL_PORT, BAUD_RATE)
        print("Starting recording...")
        
        # Calculate total samples needed
        total_samples = int(ARDUINO_SAMPLE_RATE * RECORD_DURATION)
        audio_data = []
        
        # Flush any existing data
        arduino.reset_input_buffer()
        arduino.reset_output_buffer()
        
        # Send start signal to Arduino
        arduino.write(b'S')  # Add this line
        time.sleep(0.1)     # Add this line
        
        # Record for specified duration
        start_time = time.time()
        samples_collected = 0
        
        while samples_collected < total_samples:
            if arduino.in_waiting >= 2:
                high_byte = ord(arduino.read(1))  # Changed to ord()
                low_byte = ord(arduino.read(1))   # Changed to ord()
                
                # Convert two bytes to signed 16-bit integer
                sample = (high_byte << 8) | low_byte
                if sample > 32767:
                    sample -= 65536
                    
                # Normalize to [-1, 1] for plotting
                normalized_sample = sample / 32768.0
                plot_data.append(normalized_sample)
                
                audio_data.append(sample)
                samples_collected += 1
                
                # Print progress
                if samples_collected % 100 == 0:
                    percent = (samples_collected / total_samples) * 100
                    print(f"Recording progress: {percent:.1f}%")
            
            # Check for timeout with more reasonable limit
            if time.time() - start_time > RECORD_DURATION * 1.5:  # Changed timeout
                print("Recording timed out")
                break
        
        # Convert to numpy array and save to WAV file
        samples = np.array(audio_data, dtype=np.int16)
        
        with wave.open(FILENAME, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(ARDUINO_SAMPLE_RATE)
            wav_file.writeframes(samples.tobytes())
        
        print(f"Recording saved to {FILENAME}")
        arduino.close()
        
    except Exception as e:
        print(f"Error during recording: {e}")
        traceback.print_exc()
        if 'arduino' in locals():
            arduino.close()

def main():
    try:
        # Create event to signal recording completion
        recording_complete = threading.Event()  # Add this line
        
        # Start recording in a separate thread
        record_thread = threading.Thread(target=record_audio)
        record_thread.daemon = True  # Make thread daemon
        record_thread.start()
        
        # Start the animation
        ani = FuncAnimation(fig, update_plot, interval=20, blit=True, cache_frame_data=False)  # Faster update interval
        plt.show()
        
        # Wait for recording to finish
        record_thread.join()
        
    except Exception as e:
        print(f"Error in main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 