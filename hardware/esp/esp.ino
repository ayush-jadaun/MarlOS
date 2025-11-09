/*
 * MARLOS HARDWARE "HAND"
 * Runs on ESP8266, controls an Arduino Uno
 */
#include <ESP8266WiFi.h>
#include <PubSubClient.h> // MQTT Library
                           
// ---!!--- UPDATE THESE ---!!---
const char* WIFI_SSID = "iQOO Neo7 Pro";
const char* WIFI_PASS = "HDSOAWHDHAGF";

// This is your computer's IP where Docker is running
const char* MQTT_BROKER_IP = "10.177.4.175"; 
const int MQTT_PORT = 1883;
// ---!!--------------------!!---

// This is the "address" your Python code will send commands to
const char* COMMAND_TOPIC = "marlos/devices/uno-01/command";
// This is where the hardware reports its status
const char* STATUS_TOPIC = "marlos/devices/uno-01/status";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

/*
 * This function is called when a command is received from the broker
 */
void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  // Convert payload to a String
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("Command received: ");
  Serial.println(message);

  if (message == "ON") {
    // Send a '1' to the Uno over Serial to turn the LED on
    Serial1.write('1'); 
    mqttClient.publish(STATUS_TOPIC, "LED set to ON");
  } else if (message == "OFF") {
    // Send a '0' to the Uno over Serial to turn the LED off
    Serial1.write('0'); 
    mqttClient.publish(STATUS_TOPIC, "LED set to OFF");
  } else {
    mqttClient.publish(STATUS_TOPIC, "Unknown command");
  }
}

// Reconnect to MQTT if disconnected
void reconnect() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect("esp8266-uno-01")) { // Unique client ID
      Serial.println("connected");
      // Subscribe to the command topic
      mqttClient.subscribe(COMMAND_TOPIC);
      Serial.print("Subscribed to: ");
      Serial.println(COMMAND_TOPIC);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200); // For debugging to your PC
  Serial1.begin(9600);  // For communication with the Uno
  
  // 1. Connect to WiFi
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // 2. Configure MQTT
  mqttClient.setServer(MQTT_BROKER_IP, MQTT_PORT);
  mqttClient.setCallback(mqtt_callback); // Set function to call on new message
}

void loop() {
  // 3. Keep MQTT connection alive and check for messages
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop(); 
}