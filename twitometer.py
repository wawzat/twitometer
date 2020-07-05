# Retrives top 50 trends from twitter and tweets / tweets per minute for given keywords.
# Performs rudimentary sentiment scoring
# Stepper motor gauge
# Uses Adafruit DC & Stepper Motor Bonnet for Raspberry Pi Product ID: 4280
# Uses X27.128 Automotive Instrument Stepper Motor
# Include your Twitter API Keys and Tokens in a file named config.py
# To do: for - in searches are matching partial words (i.e., lie in believe)
# James S. Lucas - 20200703
import config
import tweepy
from sys import stdout, argv
#from os import system
import datetime
from operator import itemgetter
import argparse
from smbus import SMBus
import atexit
from time import sleep

# Arduino I2C address
addr = 0x08

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


def exit_function():
    print(" ")
    print("End by atexit")
    myStream.disconnect()
    indicator_pos_1 = 0
    indicator_pos_2 = 0
    move_stepper_1(str(indicator_pos_1))
    move_stepper_2(str(indicator_pos_2))
    #system("stty echo")
    sleep(1)
    exit()


atexit.register(exit_function)


# This function converts a string to an array of bytes. 
def StringToBytes(src): 
  converted = [] 
  for b in src: 
    converted.append(ord(b)) 
    #print(converted)
  return converted


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


def writeData(value):
    try:
        byteValue = StringToBytes(value)
        #print(byteValue)
        bus.write_i2c_block_data(addr, 0x00, byteValue)
        sleep(.1)
        return -1 
    except OSError as e:
        print("Connection Broken")
        print(" ")
        pass


def move_stepper_1(indicator_pos_1):
    # Format is XYYYY where X is motor number and YYYY is 1-4 digit indicator postion
    command = "1" + indicator_pos_1
    writeData(command)


def move_stepper_2(indicator_pos_2):
    # Format is XYYYY where X is motor number and YYYY is 1-4 digit indicator postion
    command = "2" + indicator_pos_2
    writeData(command)


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
        sleep(1)


    def on_status(self, status):
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
                                self.dict_sentiment[tag] -= 1
                                self.dict_tpm_sentiment[tag] -=1
                                tweet_score -= 1
                                self.dict_sentiment["trump"] +=1
                                self.dict_tpm_sentiment["trump"] +=1
                            else:
                                self.dict_sentiment[tag] -= 1
                                self.dict_tpm_sentiment[tag] -=1
                                tweet_score -= 1
                                self.dict_sentiment["biden"] +=1
                                self.dict_tpm_sentiment["biden"] +=1
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
                elif tpm_elapsed_time.milliseconds >= 500:
                    for tag in self.tags:
                        self.dict_tpm[tag] = int(self.dict_tpm_pos_tweets[tag] / tpm_elapsed_time.milliseconds * 60000)
                if tag == "biden":
                    indicator_pos_1 = min(int(3 * self.dict_tpm[tag] + 150), 2000)
                    move_stepper_1(str(indicator_pos_1))
                if tag == "trump":
                    indicator_pos_2 = min(int(3 * self.dict_tpm[tag] + 150), 2000)
                    move_stepper_2(str(indicator_pos_2))
        for tag in self.tags:
            if self.dict_num_tweets[tag] != 0:
                sentiment_pct = round(self.dict_sentiment[tag] / self.dict_num_tweets[tag], 2)
            else:
                sentiment_pct = 0
            if (tpm_elapsed_time.seconds %5 == 0):
                message = (
                    message + tag + ": " + str(self.dict_num_tweets[tag])
                    + " / " + str(sentiment_pct)
                    + " / " + str(self.dict_pos_tweet_rate[tag])
                    + " / " + str(self.dict_tpm[tag])
                    + " / " + str(self.dict_tweet_rate[tag])
                    + " | "
                )
                stdout.write("\r | " + message + "                       ")


    def on_error(self, status_code):
        # Status code 420 is too many connections in time period. 10 second rate limit increases exponentially for each 420 error
        if status_code == 420:
            print("Error 420, Twitter rate limit in effect")
            #returning False in on_data disconnects the stream
            return False


def get_trends(args):
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
    args = get_arguments()
    tags = args.keywords
    get_trends(args)
    # Start the tweepy SteamListner.
    myStreamListener = MyStreamListener(tags)
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener, tweet_mode='extended')
    myStream.filter(track=tags, is_async=True)
    #myStream.filter(track=tags)
    print(" ")
except KeyboardInterrupt:
    print(" ")
    print("End by Ctrl-C")
    myStream.disconnect()
    indicator_pos_1 = 0
    indicator_pos_2 = 0
    move_stepper_1(str(indicator_pos_1))
    move_stepper_2(str(indicator_pos_2))
    sleep(1)
    exit()