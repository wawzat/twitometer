# Retrives top trends from twitter and tweets / tweets per minute for given keywords.
# Performs rudimentary sentiment scoring
# Stepper motor gauge
# Uses X27.128 Automotive Instrument Stepper Motor with Arduino and AX1201728SG quad driver.
# Include your Twitter API Keys and Tokens in a file named config.py
# To do: for - in searches are matching partial words (i.e., lie in believe)
# James S. Lucas - 20200808
import RPi.GPIO as GPIO
from datetime import date
import config
import tweepy
from sys import stdout, argv
import datetime
from operator import itemgetter
import argparse
from smbus import SMBus
import atexit
from time import sleep
import statistics
from random import randint
#import re
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT


pwr_pin = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(pwr_pin, GPIO.OUT)
GPIO.output(pwr_pin, GPIO.LOW)


# Stepper Arduino I2C address
addr_stepper = 0x08

# LED Matrix Arduino I2C address
addr_led = 0x06

bus = SMBus(1)

# twitter API keys stored in config.py
API_KEY = config.API_KEY 
API_SECRET = config.API_SECRET 
ACCESS_TOKEN = config.ACCESS_TOKEN 
ACCESS_TOKEN_SECRET = config.ACCESS_TOKEN_SECRET

# tweepy auth for twitter
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


num_i2c_errors = 0
last_i2c_error_time = datetime.datetime.now()


def exit_function():
    '''Function disconnects stream and resets motor positions to zero. 
    Called by exception handler'''
    print(" ")
    print("End by atexit")
    global pwr_pin
    myStream.disconnect()
    indicator_pos_1 = 0
    indicator_pos_2 = 0
    write_time = datetime.datetime.now()
    sleep(.3)
    write_time = move_stepper(str(indicator_pos_1), str(indicator_pos_2), write_time)
    sleep(.8)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pwr_pin, GPIO.OUT)
    GPIO.output(pwr_pin, GPIO.LOW)
    GPIO.cleanup()
    sleep(.5)
   #system("stty echo")
    exit()


atexit.register(exit_function)


def get_arguments():
    parser = argparse.ArgumentParser(
    description='get current trends and stats for given topics from Twitter.',
    prog='twit_stream',
    usage='%(prog)s [-l <locations>] [-k <keywords>]',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g=parser.add_argument_group(title='arguments',
          description='''   -l, --locations <trend location(s)>     optional.  enter trend locations.
   -k, --keywords <keywords>               optional.  enter keywords to search in stream.         ''')
    g.add_argument('-l', '--locations',
                    type=str,
                    default=['USA'],
                    nargs = '*',
                    choices = [
                        'World', 'NYC', 'LA', 'USA'
                        ],
                    metavar='',
                    dest='locations',
                    help=argparse.SUPPRESS)
    g.add_argument('-k', '--keywords',
                    type=str,
                    default=['biden', 'trump', 'dnc', 'rnc'],
                    nargs = '*',
                    metavar='',
                    dest='keywords',
                    help=argparse.SUPPRESS)
    args = parser.parse_args()
    return(args)


def i2c_error_tracker():
    global last_i2c_error_time
    global num_i2c_errors
    global pwr_pin
    duration_since_last_error = datetime.datetime.now() - last_i2c_error_time
    last_i2c_error_time = datetime.datetime.now()
    if duration_since_last_error.total_seconds() <= 2:
        num_i2c_errors += 1
        print(str(num_i2c_errors))
    elif duration_since_last_error.total_seconds() > 2:
        num_i2c_errors = 0
    if num_i2c_errors > 2:
        num_i2c_errors = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pwr_pin, GPIO.OUT)
        GPIO.output(pwr_pin, GPIO.LOW)
        sleep(2)
        GPIO.output(pwr_pin, GPIO.HIGH)
        sleep(2)


def StringToBytes(src): 
    '''Function converts a string to an array of bytes'''
    converted = [] 
    for b in src: 
        converted.append(ord(b)) 
        #print(converted)
    return converted


def writeData(motor_num, value):
    '''Function writes the command string to the  Stepper Arduino'''
    try:
        byteValue = StringToBytes(value)
        #print(byteValue)
        bus.write_i2c_block_data(addr_stepper, motor_num, byteValue)
        #sleep(.02)
    except OSError as e:
        print("Stepper I2C Communication Error")
        print(" ")
        i2c_error_tracker()
        pass


def write_matrix(msg, display_num, led_write_time):
    '''Function writes the command string to the LED Arduino'''
    try:
        byteValue = StringToBytes(msg)
        num_chars = len(byteValue)
        num_whole_blocks, chars_in_last_block = divmod(num_chars, 30)
        if chars_in_last_block > 0:
            num_blocks = num_whole_blocks + 1
        else:
             num_blocks = num_whole_blocks
        for b in range(num_blocks):
            if b <= (num_blocks - 2):
                #rem_chars = num_chars - ((b + 1) * 30)
                strt_range = b * 30
                end_range = strt_range + 30
                msg = byteValue[strt_range : end_range]
                bus.write_i2c_block_data(addr_led, 0x01, msg)
                sleep(.02)
            else:
                #rem_chars = 0
                strt_range = b * 30
                end_range = num_chars
                msg = byteValue[strt_range : end_range]
                msg.append(ord(display_num))
                print(str(strt_range) + "/" + str(end_range) + "/" + str(len(msg)))
                bus.write_i2c_block_data(addr_led, 0x02, msg)
                led_write_time = datetime.datetime.now()
                sleep(.02)
        #test_msg = "Test Message"
        #print(" ")
        #print(byteValue)
        #Truncate byteValue to 32 bits
        #byteValue_trunc = byteValue[0:31]
        #sleep(.25)
        return led_write_time
    except OSError as e:
        #led_write_time = datetime.datetime.now()
        print("LED Matrix I2C Communication Error")
        print(" ")
        return led_write_time
        pass


def move_stepper(indicator_pos_1, indicator_pos_2, write_time):
    '''Function prepares the command string and sends to WriteData()'''
    # Format is XYYYY where X is motor number and YYYY is 1-4 digit indicator postion
    elapsed_time = datetime.datetime.now() - write_time
    if elapsed_time.total_seconds() > .2:
        #command = indicator_pos_1
        motor_num = 0x01 
        position = indicator_pos_1
        writeData(motor_num, position)
        #print("B: " + str(indicator_pos_2))
        sleep(.0002)
        motor_num = 0x02
        position = indicator_pos_2
        writeData(motor_num, position)
        #print("T: " + str(indicator_pos_2))
        write_time = datetime.datetime.now()
    return write_time


# tweepy SteamListner Class
class MyStreamListener(tweepy.StreamListener):
    def __init__(self, tags):
        super(MyStreamListener, self).__init__()
        self.start_time = datetime.datetime.now() 
        self.last_update_time = datetime.datetime.now()
        self.tags = tags
        self.dict_num_tweets = { i : 0 for i in self.tags}
        self.dict_tweet_rate = { i : 0 for i in self.tags}
        self.dict_tpm_num_tweets = { i : 0 for i in self.tags}
        self.dict_sentiment = { i : 0 for i in self.tags}
        self.dict_tpm = { i : 0 for i in self.tags}
        self.dict_pos_tweets = { i : 0 for i in self.tags}
        self.dict_tpm_sentiment = { i : 0 for i in self.tags}
        self.dict_tpm_pos_tweets = { i : 0 for i in self.tags}
        self.dict_pos_tweet_rate = { i : 0 for i in self.tags}
        self.stepper_write_time = datetime.datetime.now()
        self.led_write_time_1 = datetime.datetime.now()
        self.led_write_time_2 = datetime.datetime.now()
        self.indicator_pos_1 = 0
        self.indicator_pos_2 = 0
        self.indicator_pos_1_list = []
        self.indicator_pos_2_list = []
        self.positive_words = [
            'amazing', 'beautiful', 'begin', 'best', 'better', 'celebrate', 'celebrating', 'creative', 'fabulous',
            'fight', 'God bless', 'great', 'growth', 'happy', 'incredible', 'leader', 'pleased', 'positive', 'potential',
            'strong economy', 'superb', 'support biden', 'support trump',
            'voting', 'voteblue', 'votered', 'votejoebiden', 'votedonaldtrump',
            'win', 'wonderful', 'trump2020', 'biden2020'
            ]
        self.negative_words = [
            'against', 'afraid', 'anyone voting', 'bad', 'bs', 'cheat', 'cheeto', 'creepy', 'crying', 'deny', 'demented',
            'detest', 'despite',
            'devisive', 'embarrass', 'enough', 'evil', 'fail', 'fake', 'fascist', 'feeble', 'fraud', 'garbage', 'hell', 'horrible',
            'homophobe', 'hoax', 'idiot', 'incompetent', 'insane',
            'leftist', 'liar', 'lying', 'loser', 'losing', 'misinformation', 'neverbiden', 'nevertrump',
            'outrage', 'orange', 'painful', 'pedophile', 'problem',
            'racism', 'racist', 'rapist', 'rid', 'senile', 'stupid', 'sleepy', 'sucks', 'traitor', 'traitortrump',
            'upset', 'useless', 'waste', 'weak', 'wing', 'worst',
            '#incompetent', '#traitor' 
            ]            
        sleep(2)


    def on_status(self, status):
        '''Function executes when Tweet received'''
        tweet_score = 0
        tpm_elapsed_time = datetime.datetime.now() - self.last_update_time
        elapsed_time = datetime.datetime.now() - self.start_time
        message = ""
        try:
            tweet = status.extended_tweet["full_text"]
        except AttributeError:
            tweet = status.text
        for tag in self.tags:
            if not tweet.startswith('RT'):
                if tag.upper() in tweet.upper():
                    self.dict_num_tweets[tag] += 1
                    self.dict_tpm_num_tweets[tag] += 1
                    for pos_word in self.positive_words:
                        if pos_word.upper() in tweet.upper():
                            self.dict_sentiment[tag] += 1
                            self.dict_tpm_sentiment[tag] +=1
                            tweet_score += 1
                            break
                    for neg_word in self.negative_words:
                        if neg_word.upper() in tweet.upper():
                            if tag == "biden":
                                tweet_1 = tweet
                                self.dict_sentiment[tag] -= 1
                                self.dict_tpm_sentiment[tag] -=1
                                tweet_score -= 1
                                self.dict_sentiment["trump"] +=1
                                self.dict_tpm_sentiment["trump"] +=1
                                led_elapsed_time_1 = datetime.datetime.now() - self.led_write_time_1
                                if led_elapsed_time_1.seconds >= (45 + randint(1, 10)) :
                                    self.led_write_time_1 = write_matrix(tweet_1, "1", self.led_write_time_1)
                            elif tag == "trump":
                                tweet_2 = tweet
                                self.dict_sentiment[tag] -= 1
                                self.dict_tpm_sentiment[tag] -=1
                                tweet_score -= 1
                                self.dict_sentiment["biden"] +=1
                                self.dict_tpm_sentiment["biden"] +=1
                                led_elapsed_time_2 = datetime.datetime.now() - self.led_write_time_2
                                if led_elapsed_time_2.seconds >= (46 + randint(1, 10)):
                                    self.led_write_time_2 = write_matrix(tweet_2, "0", self.led_write_time_2)
                            break
                    if self.dict_tpm_sentiment[tag] >= 0:
                        self.dict_tpm_pos_tweets[tag] = self.dict_tpm_num_tweets[tag]
                    elif self.dict_tpm_sentiment[tag] < 0:
                        self.dict_tpm_pos_tweets[tag] = self.dict_tpm_num_tweets[tag] + self.dict_tpm_sentiment[tag]
                    if self.dict_sentiment[tag] >= 0:
                        self.dict_pos_tweets[tag] = self.dict_num_tweets[tag]
                    elif self.dict_sentiment[tag] < 0:
                        self.dict_pos_tweets[tag] = self.dict_num_tweets[tag] + self.dict_sentiment[tag]
                self.dict_tweet_rate[tag] = round(self.dict_num_tweets[tag] / elapsed_time.seconds * 60)
                self.dict_pos_tweet_rate[tag] = int(self.dict_pos_tweets[tag] / elapsed_time.seconds * 60)
                tpm_elapsed_time = datetime.datetime.now() - self.last_update_time
                if tpm_elapsed_time.seconds > 8:
                    for tag in self.tags:
                        self.dict_tpm[tag] = int(self.dict_tpm_pos_tweets[tag] / tpm_elapsed_time.seconds * 60)
                        self.last_update_time = datetime.datetime.now()
                        self.dict_tpm_num_tweets[tag] = 0
                        self.dict_tpm_sentiment[tag] = 0
                        self.dict_tpm_pos_tweets[tag] = 0
                if tpm_elapsed_time.seconds >= 1:
                    for tag in self.tags:
                        self.dict_tpm[tag] = int(self.dict_tpm_pos_tweets[tag] / tpm_elapsed_time.seconds * 60 )
                        if tag == "biden":
                            self.indicator_pos_1 = min(int(4 * self.dict_tpm[tag] + 150), 3240)
                            if len(self.indicator_pos_1_list) >= 40:
                                self.indicator_pos_1_list.pop(0)
                            self.indicator_pos_1_list.append(self.indicator_pos_1)
                        elif tag == "trump":
                            self.indicator_pos_2 = min(int(4 * self.dict_tpm[tag] + 150), 3240)
                            if len(self.indicator_pos_2_list) >= 40:
                                self.indicator_pos_2_list.pop(0)
                            self.indicator_pos_2_list.append(self.indicator_pos_2)
                position1 = int(statistics.mean(self.indicator_pos_1_list))
                position2 = int(statistics.mean(self.indicator_pos_2_list))
                self.stepper_write_time = move_stepper(str(position1), str(position2), self.stepper_write_time)
        for tag in self.tags:
            if self.dict_num_tweets[tag] != 0:
                sentiment_pct = round(self.dict_sentiment[tag] / self.dict_num_tweets[tag], 2)
            else:
                sentiment_pct = 0
            if (tpm_elapsed_time.seconds %2 == 0):
                message = (
                    message + tag + ": " + str(self.dict_num_tweets[tag])
                    + " / " + str(sentiment_pct)
                    + " / " + str(self.dict_pos_tweet_rate[tag])
                    + " / " + str(self.dict_tpm[tag])
                    + " / " + str(self.dict_tweet_rate[tag])
                    + " | "
                )
                stdout.write("\r | " + message + "                       ")
                #print(" | " + message)


    def on_error(self, status_code):
        # Status code 420 is too many connections in time period. 10 second rate limit increases exponentially for each 420 error
        if status_code == 420:
            print("Error 420, Twitter rate limit in effect")
            #returning False in on_data disconnects the stream
            return False


def get_trends(args):
    '''Function runs once at start, gets and prints top trends'''
    WOEID_dict = {'World': 1, 'NYC': 2459115, 'LA': 2442047, 'USA': 23424977}
    locations = args.locations
    for location in locations:
        data = api.trends_place(WOEID_dict.get(location), '#')
        trends = data[0]["trends"]
        # Remove trends with no Tweet volume data
        trends = filter(itemgetter("tweet_volume"), trends)
        sorted_trends = sorted(trends, key=itemgetter("tweet_volume"), reverse=True)
        names = [trend['name'] for trend in sorted_trends]
        trends_names = ' | '.join(names)
        print(" ")
        print(location)
        print("| " + trends_names + " |")


# Main
try:
    GPIO.output(pwr_pin, GPIO.HIGH)
    sleep(2)
    args = get_arguments()
    tags = args.keywords
    get_trends(args)
    # Start the tweepy SteamListner.
    myStreamListener = MyStreamListener(tags)
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener, tweet_mode='extended')
    #myStream.filter(track=tags, is_async=True)
    myStream.filter(track=tags)
    print(" ")
except KeyboardInterrupt:
    print(" ")
    print("End by Ctrl-C")
    myStream.disconnect()
    indicator_pos_1 = 0
    indicator_pos_2 = 0
    write_time = datetime.datetime.now()
    write_time = move_stepper(str(indicator_pos_1), str(indicator_pos_2), write_time)
    sleep(2)
    GPIO.output(pwr_pin, GPIO.LOW)
    GPIO.cleanup()
    sleep(1)
    exit()