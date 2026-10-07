import serial
import numpy as np
import wave
import time
import traceback
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import threading
from scipy.signal import butter, sosfilt, iirnotch
from scipy.interpolate import interp1d

# Configure settings
SERIAL_PORT = '/dev/tty.YOUR_DEVICE'
BAUD_RATE = 115200
ARDUINO_SAMPLE_RATE = 800  # Original Arduino sampling rate
AUDIO_SAMPLE_RATE = 44100  # Standard audio sample rate
RECORD_DURATION = 10  # Recording duration in seconds
FILENAME = "stethoscope_recording.wav"
PLOT_LENGTH = 1000  # Number of points to display
FILTER_LOW = 60       # Lowered for less resonance
FILTER_HIGH = 1000    # Adjusted for voice
FILTER_ORDER = 2      # Reduced order for gentler filtering
CHUNK_SIZE = 100

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

def create_bandpass_filter(lowcut=FILTER_LOW, highcut=FILTER_HIGH, fs=ARDUINO_SAMPLE_RATE, order=FILTER_ORDER):
    """Gentler bandpass filter with lower order"""
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    
    low = max(0.001, min(0.99, low))
    high = max(0.001, min(0.99, high))
    if high <= low:
        high = low + 0.001
    
    # Use Butterworth filter for smoother frequency response
    sos = butter(order, [low, high], btype='band', output='sos', analog=False)
    return sos

def apply_filter(data, sos):
    """Apply filter with envelope-based smoothing"""
    # Calculate signal envelope
    envelope = np.abs(data)
    envelope = np.convolve(envelope, np.ones(10)/10, mode='same')
    
    # Apply filter
    filtered = sosfilt(sos, data)
    
    # Smooth transition based on envelope
    threshold = np.mean(envelope) * 2
    mask = envelope > threshold
    
    # Blend filtered and original signal based on envelope
    result = np.zeros_like(filtered)
    result[mask] = filtered[mask] * 0.8 + data[mask] * 0.2  # More filtered during speech
    result[~mask] = filtered[~mask] * 0.2 + data[~mask] * 0.8  # Less filtered during silence
    
    return result

def record_audio():
    try:
        arduino = connect_to_arduino(SERIAL_PORT, BAUD_RATE)
        print("Starting recording...")
        
        total_samples = int(ARDUINO_SAMPLE_RATE * RECORD_DURATION)
        audio_data = []
        
        sos = create_bandpass_filter()
        
        arduino.reset_input_buffer()
        arduino.reset_output_buffer()
        
        arduino.write(b'S')
        time.sleep(0.1)
        
        start_time = time.time()
        samples_collected = 0
        buffer = []
        
        while samples_collected < total_samples:
            if arduino.in_waiting >= 2:
                high_byte = ord(arduino.read(1))
                low_byte = ord(arduino.read(1))
                
                sample = (high_byte << 8) | low_byte
                if sample > 32767:
                    sample -= 65536
                
                buffer.append(sample)
                samples_collected += 1
                
                if len(buffer) >= CHUNK_SIZE:
                    # Process chunk with envelope-aware filtering
                    chunk = np.array(buffer, dtype=np.float32)
                    chunk = chunk / 32768.0  # Normalize to [-1, 1]
                    
                    filtered_chunk = apply_filter(chunk, sos)
                    
                    # Update plot
                    for sample in filtered_chunk:
                        plot_data.append(sample)
                    
                    # Store processed data
                    audio_data.extend(filtered_chunk * 32768.0)
                    buffer = []
                
                if samples_collected % 100 == 0:
                    percent = (samples_collected / total_samples) * 100
                    print(f"Recording progress: {percent:.1f}%")
            
            if time.time() - start_time > RECORD_DURATION * 1.2:
                print("Recording timed out")
                break
        
        # Process remaining samples
        if buffer:
            chunk = np.array(buffer, dtype=np.float32) / 32768.0
            filtered_chunk = apply_filter(chunk, sos)
            audio_data.extend(filtered_chunk * 32768.0)
        
        # Convert to numpy array and normalize
        samples = np.array(audio_data, dtype=np.float32)
        
        # Gentle normalization
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples * (30000 / max_val)
        
        # Save to WAV file
        with wave.open(FILENAME, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(ARDUINO_SAMPLE_RATE)
            wav_file.writeframes(samples.astype(np.int16).tobytes())
        
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