/* Example code for scrolling text effect on MAX7219 LED dot matrix display with Arduino. More info: https://www.makerguides.com */

// Include the required LED libraries:
#include <MD_Parola.h>
#include <MD_MAX72xx.h>
#include <SPI.h>

#include <Wire.h>

// Define hardware type, size, and output pins:
#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
#define MAX_DEVICES 8
#define num_zones 2
#define CS_PIN 10

// Create a new instance of the MD_Parola class with hardware SPI connection:
MD_Parola myDisplay = MD_Parola(HARDWARE_TYPE, CS_PIN, MAX_DEVICES);

// Define the I2C address of this device for receiving data from Raspberry Pi
#define addr 0x06

char msg[511];
char msg_0[511];
char msg_1[511];
int char_pos = 0;
int block_count = 0;
int block_flag = 0;

void setup() {
  Serial.begin(9600);
  // begin running as an I2C slave on the specified address
  Wire.begin(addr);
 
  // create event for receiving data
  Wire.onReceive(receiveEvent);

  // Intialize the LED object:
  myDisplay.begin(num_zones);
  //myDisplay.begin();

  // Setup display zones
  myDisplay.setZone(0, 0, 3);
  myDisplay.setZone(1, 4, 7);
  
  // Set the intensity (brightness) of the display (0-15):
  myDisplay.setIntensity(0);
  // Clear the display:
  myDisplay.displayClear();
}


// Function that executes whenever data is received from master
void receiveEvent(int howMany) {
  int loop_overrun = 0;
  while (Wire.available()) {
    if (block_count == 0) {
      // First byte is cmd byte = 1 or 2. 2 means it is the last block in the message.
      block_flag = Wire.read();
      block_count++;
    }
    // from the second byte on
    else {
      char c = Wire.read();
      msg[char_pos] = (char)c;
      char_pos++;
      msg[char_pos] = '\0';
      if (char_pos >= 289) {
        char_pos = 0;
        //block_flag = 0;
        //block_count = 0;
        //msg[0] = '\0';
        //loop_overrun = 1;
        Serial.println("Loop Overrun");
      }
    }
    //if (loop_overrun == 1) {
      //loop_overrun = 0;
      //break;
    //}
  }
  if (block_flag == 2) {
    char display_num_char = msg[char_pos - 1];
    int display_num = display_num_char - '0';
    msg[char_pos - 1] = '\0';
    if (display_num == 0) {
      strcpy( msg_0, msg );
    }
    if (display_num == 1) {
      strcpy( msg_1, msg );
    }
    // Done receiving the last block in the message. Display it.
    char_pos = 0;
    Serial.println(display_num);
    Serial.println(msg);
    myDisplay.displayClear();
    if (display_num == 0) {
      myDisplay.displayZoneText(display_num, msg_0, PA_CENTER, 30, 0, PA_SCROLL_LEFT, PA_SCROLL_LEFT);
    }
    if (display_num == 1) {
      myDisplay.displayZoneText(display_num, msg_1, PA_CENTER, 30, 0, PA_SCROLL_LEFT, PA_SCROLL_LEFT);
    }
    msg[0] = '\0';
  }
  block_count = 0;
  block_flag = 0;
}


void loop() {
  if (myDisplay.displayAnimate()) {
    myDisplay.displayReset();
  }
}
