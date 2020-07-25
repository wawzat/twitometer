//Receives bytes from Raspberry Pi in the format XYYYY where X is the motor number and YYYY is the desired motor position.
//YYYY is variable length from 1 to 3240 (270 Deg)
//James S. Lucas 20200705
#include <SwitecX12.h>
#include <Wire.h>
const int STEPS = 315 * 12;
const int A_STEP = 8;
const int A_DIR = 2;
const int B_STEP = 4;
const int B_DIR = 7;
const int RESET = 12;

//int redLED01 = 3;
//int greenLED01 = 5;
//int blueLED01 = 6;

//int redLED02 = 9;
//int greenLED02 = 10;
//int blueLED02 = 11;

SwitecX12 motor1(STEPS, A_STEP, A_DIR);
SwitecX12 motor2(STEPS, B_STEP, B_DIR);

//Arduino code to receive I2C communication from Raspberry Pi

// Define the I2C address of this device.
#define addr 0x08

void setup(void) {
  digitalWrite(RESET, HIGH);
  Serial.begin(9600);
  motor1.zero();
  motor2.zero();

  //pinMode(redLED01, OUTPUT);
  //pinMode(greenLED01, OUTPUT);
  //pinMode(blueLED01, OUTPUT);
  //pinMode(redLED02, OUTPUT);
  //pinMode(greenLED02, OUTPUT);
  //pinMode(blueLED02, OUTPUT);

  // begin running as an I2C slave on the specified address
  Wire.begin(addr);
 
  // create event for receiving data
  Wire.onReceive(receiveEvent);
}


//Global variables for position
int position1 = 0;
int position2 = 0;


//void RGBColor01 (int redValue, int greenValue, int blueValue) {
  //analogWrite(redLED01, redValue);
  //analogWrite(greenLED01, greenValue);
  //analogWrite(blueLED01, blueValue);
//}


//void RGBColor02 (int redValue, int greenValue, int blueValue) {
  //analogWrite(redLED02, redValue);
  //analogWrite(greenLED02, greenValue);
  //analogWrite(blueLED02, blueValue);
//}


// Function that executes whenever data is received from master
void receiveEvent(int howMany) {
  String cmdString = "";
  String posString = "";
  String motorNumString = "";
  //Serial.println("Data Received");
  while (Wire.available()) { // loop through all but the last
    char c = Wire.read(); // receive byte as a character
    cmdString += (char)c;
  }


//Parse the command into motor number and position
  cmdString.remove(0,1);
  
  motorNumString = cmdString;
  motorNumString.remove(1);

  posString = cmdString;
  posString.remove(0,1);

  if (motorNumString == "1") {
    position1 = posString.toInt();
  }
  else if (motorNumString == "2") {
    position2 = posString.toInt();
  }
  cmdString = "";
  //Serial.println(position1);
}

void loop(void) {
  //RGBColor01(0, 0, 255); //blue
  //RGBColor02(255, 0, 0); //red
 
  motor1.setPosition(position1);
  motor2.setPosition(position2);

  motor1.update();
  motor2.update();
}
