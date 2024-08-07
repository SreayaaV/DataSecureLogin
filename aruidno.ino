const int ledPin = 13;
const int buzzerPin = 10;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  Serial.println("Setup complete");
}

void loop() {
  if(Serial.available()>0){
    char command=Serial.read();
  
  if (command == '1' || command == '2') { // Activate for both regular and admin users
      Serial.println("Activating LED-AUTHORISED LOGIN");
      digitalWrite(ledPin, HIGH);
      delay(9000);
      digitalWrite(ledPin, LOW);
    } else if (command == '3') { // Activate buzzer for unauthorized access attempts
      Serial.println("Activating buzzer-AUTHORISED LOGIN");
      tone(buzzerPin, 5000); // Start buzzing
      delay(9000); // Buzz for 5 seconds
      noTone(buzzerPin); // Stop buzzing
    } else {
      Serial.println("Invalid command");
    }
  }
}