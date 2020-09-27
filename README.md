# Twitometer  

## Operation  
1. Raspberry Pi establishes a Twitter Streaming API via Tweepy.  
2. Tweets are retrieved that include text that match a series of words (Biden Trump).  
3. "Tweets per minute" is calculated and sent to one of two Arduino's via I2C.  
4. The Arduino outputs a pulse for each microstep to a microstepping controller which is connected to an X27-168 instrumentation stepper.  
5. Periodically  the text of a tweet corresponding to a keyword (Trump or Biden) is sent to the second Arduino via I2C.  
6. The second Arduino sends the text over I2C one of two corresponding MAX7219 8x32 LED matrices (blue for Biden, red for Trump).  
7. The corresponding tweet scrolls across each display.  

## Future improvements   
1. Naive attempt to classify tweets as "positive" or "negative" by comparison to lists of "positive" or "negative" words doesn't work very well.   
2. Left over unused variables and code fragments need to be cleaned up.  
3. I2C communications might benefit from more robust error checking and flow control. Periodic I2C errors still exist.  
4. Periodically scrolling text appears to be garbled or truncated.  
5. If too many I2C errors occur in succession, the PI brute force reboots the Arduinos by cycling the power.  
6. Basic de-amateurization.  
 

## Schematic Diagram  
[fritzing](/doc/fritzing.png)