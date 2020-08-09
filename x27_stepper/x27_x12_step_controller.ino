//Receives bytes from Raspberry Pi in the format XYYYY where X is the motor number and YYYY is the desired motor position.
//YYYY is variable length from 1 to 3240 (270 Deg)
//James S. Lucas 20200726
#include <SwitecX12.h>
#include <Wire.h>
const int STEPS = 315 * 12;
const int A_STEP = 8;
const int A_DIR = 2;
const int B_STEP = 4;
const int B_DIR = 7;
const int RESET = 12;

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

  // begin running as an I2C slave on the specified address
  Wire.begin(addr);
 
  // create event for receiving data
  Wire.onReceive(receiveEvent);
}


//Global variables for position
int position1 = 0;
int position2 = 0;


// Function that executes whenever data is received from master
void receiveEvent(int howMany) {
  char cmd[16];
  char buffer[5];
  int motor_num;
  int char_pos = 0;
  while (Wire.available()) { // loop through all but the last
    char c = Wire.read(); // receive byte as a character
    cmd[char_pos] = (char)c;
    char_pos++;
    cmd[char_pos] = '\0';
  }
  char_pos = 0;


//Parse the command into motor number and position
  motor_num = cmd[0];
  buffer[0] = cmd[1];
  buffer[1] = cmd[2];
  buffer[2] = cmd[3];
  buffer[3] = cmd[4];
  buffer[4] = '\0';

  if (motor_num == 1) {
    position1 = atoi(buffer);
  }
  else if (motor_num == 2) {
    position2 = atoi(buffer);
  }
}


void loop(void) {
 
  motor1.setPosition(position1);
  motor2.setPosition(position2);

  motor1.update();
  motor2.update();
}
