Twitometer  

Operation  
Raspberry Pi establishes a Twitter Streaming API via Tweepy.  
Tweets are retrieved that include text that match a series of words (Biden Trump).  
"Tweets per minute" is calculated and sent to one of two Arduino's via I2C.  
The Arduino outputs a pulse for each microstep to a microstepping controller which is connected to an X27-168 instrumentation stepper.  
Periodically  the text of a tweet corresponding to a keyword (Trump or Biden) is sent to the second Arduino via I2C.  
The second Arduino sends the text over I2C one of two corresponding MAX7219 8x32 LED matrices (blue for Biden, red for Trump).  
The corresponding tweet scrolls across each display.  

Future improvements   
Naive attempt to classify tweets as "positive" or "negative" by comparison to lists of "positive" or "negative" words doesn't work very well.   
Left over unused variables and code fragments need to be cleaned up.  
I2C communications might benefit from more robust error checking and flow control. Periodic I2C errors still exist.  
Periodically scrolling text appears to be garbled or truncated.  
If too many I2C errors occur in succession, the PI brute force reboots the Arduinos by cycling the power.  
Basic de-amateurization.  
 

Schematic Diagram  
[fritzing](doc/fritzing.png)