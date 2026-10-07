const int micPin = A0;  // Analog pin for microphone
const int sampleRate = 8000;  // Sampling rate in Hz
const unsigned long sampleInterval = 1000000 / sampleRate;  // Interval in microseconds

void setup() {
  Serial.begin(115200);  // High baud rate for better performance
}

void loop() {
  static unsigned long lastSampleTime = 0;
  
  if (micros() - lastSampleTime >= sampleInterval) {
    int sample = analogRead(micPin);
    Serial.write(sample >> 2);  // Convert 10-bit to 8-bit and send
    lastSampleTime += sampleInterval;
  }
} 