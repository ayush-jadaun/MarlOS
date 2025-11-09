// Arduino Uno LED Controller Code
// Connect the ESP8266's Serial (TX/RX) to the Uno's Serial (RX/TX)
// Connect the LED to pin 13 (or change the pin)

int ledPin = 13; // The built-in LED

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600); // Must match Serial1.begin(9600) on ESP
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command == '1') {
      digitalWrite(ledPin, HIGH); // Turn LED ON
    } else if (command == '0') {
      digitalWrite(ledPin, LOW); // Turn LED OFF
    }
  }
}