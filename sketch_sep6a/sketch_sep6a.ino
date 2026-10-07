const int micPin = A0;  // Microphone connected to A0

void setup() {
  Serial.begin(115200);  // Start serial communication at 115200 baud
}

void loop() {
  int sample = analogRead(micPin);  // Read analog value from microphone
  
  // Print the value to Serial for plotting (range 0-1023)
  Serial.println(sample);  // This is the value to plot

  delay(10);  // Small delay to avoid overwhelming the Serial Plotter
}
