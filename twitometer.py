# Retrives top 50 trends from twitter and tweets / tweets per minute for given keywords.
# Performs rudimentary sentiment scoring
# Stepper motor gauge
# Uses Adafruit DC & Stepper Motor Bonnet for Raspberry Pi Product ID: 4280
# Uses X27.128 Automotive Instrument Stepper Motor
# Include your Twitter API Keys and Tokens in a file named config.py
# To do: for - in searches are matching partial words (i.e., lie in believe)
# James S. Lucas - 20200617
import config
import tweepy
from sys import stdout, argv
import datetime
from operator import itemgetter
import argparse
from adafruit_motor import stepper
from adafruit_motorkit import MotorKit
import atexit
from time import sleep

kit = MotorKit()

kit.stepper1.release()
kit.stepper2.release()
sleep(2)

def turnOffMotors():
    kit.stepper1.release()
    kit.stepper2.release()

atexit.register(turnOffMotors)

delay = .01
#import csv
#from Raspi_X27_Stepper import Raspi_MotorHAT, Raspi_StepperMotor
#from Raspi_X27_Stepper import Raspi_MotorHAT, Raspi_StepperMotor

# create a default  stepper motor object, no changes to I2C address or frequency
#mh = Raspi_MotorHAT(0x6F)

#myStepper = mh.getStepper(600, 1)  	# 600 steps/rev, motor port #1 (M1 + M2)
#myStepper.setSpeed(50)  		# 120 RPM

# twitter API keys:
API_KEY = config.API_KEY 
API_SECRET = config.API_SECRET 
ACCESS_TOKEN = config.ACCESS_TOKEN 
ACCESS_TOKEN_SECRET = config.ACCESS_TOKEN_SECRET

# tweepy auth for twitter
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


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


def move_stepper_1(sentiment_1, current_position_1):
    if sentiment_1 >= 2400:
        sentiment_1 = 2400
    desired_position = int(sentiment_1 * .25)
    if desired_position >= current_position_1:
        steps = desired_position - current_position_1
        for i in range(steps):
            kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
            sleep(delay)
        #myStepper.step(steps, Raspi_MotorHAT.FORWARD, Raspi_MotorHAT.SINGLE)
        current_position_1 = current_position_1 + steps
    elif current_position_1 > desired_position:
        steps = current_position_1 - desired_position
        for i in range(steps):
            kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            sleep(delay)
        current_position_1 = current_position_1 - steps
    return current_position_1


def move_stepper_2(sentiment_2, current_position_2):
    if sentiment_2 >= 2400:
        sentiment_2 = 2400
    desired_position = int(sentiment_2 * .25)
    if desired_position >= current_position_2:
        steps = desired_position - current_position_2
        for i in range(steps):
            kit.stepper2.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
            sleep(delay)
        #myStepper.step(steps, Raspi_MotorHAT.FORWARD, Raspi_MotorHAT.SINGLE)
        current_position_2 = current_position_2 + steps
    elif current_position_2 > desired_position:
        steps = current_position_2 - desired_position
        for i in range(steps):
            kit.stepper2.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            sleep(delay)
        current_position_2 = current_position_2 - steps
    return current_position_2


# tweepy SteamListner Class
class MyStreamListener(tweepy.StreamListener):
    def __init__(self, tags):
        super(MyStreamListener, self).__init__()
        self.start_time = datetime.datetime.now() 
        self.last_gauge_time_1 = datetime.datetime.now()
        self.last_gauge_time_2 = datetime.datetime.now()
        self.tags = tags
        self.dict_num_tweets = { i : 0 for i in self.tags}
        self.dict_tweet_rate = { i : 0 for i in self.tags}
        self.dict_sentiment = { i : 0 for i in self.tags}
        self.dict_pos_tweets = { i : 0 for i in self.tags}
        self.dict_pos_tweet_rate = { i : 0 for i in self.tags}
        self.current_position_1 = 0
        self.current_position_2 = 0

    def on_status(self, status):
        #print(status.text)
        #csv_output_file = r"D:\Users\James\OneDrive\Documents\Raspberry Pi-Matrix5\JSL Python Code\Twitter\tweets.csv"
        #row = []
        tweet_score = 0
        positive_words = [
            'amazing', 'beautiful', 'begin', 'best', 'better', 'celebrate', 'celebrating', 'creative', 'fabulous',
            'fight', 'great', 'happy', 'incredible', 'leader', 'pleased', 'positive', 'potential', 'ready',
            'superb', 'support biden', 'support trump', 'voting', 'win', 'wonderful', 'trump2020', 'biden2020'
            ]
        negative_words = [
            'against', 'afraid', 'anyone voting', 'bad', 'bs', 'cheat', 'cheeto', 'creepy', 'crying', 'deny', 'detest', 'despite',
            'devisive', 'embarrass', 'evil', 'fail', 'fake', 'feeble', 'fraud', 'fuck', 'garbage', 'hell', 'homophobe', 'hoax', 'idiot',
            'leftist', 'liar', 'lying', 'loser', 'losing', 'misinformation', 'not', 'outrage', 'orange', 'painful', 'pedophile',
            'racism', 'racist', 'rapist', 'rid', 'shit', 'stupid', 'sleepy', 'sucks',
            'upset', 'useless', 'waste', 'weak', 'wing', 'worst'
            ]
        elapsed_time = datetime.datetime.now() - self.start_time
        if elapsed_time.seconds > 1:
            message = ""
            try:
                tweet = status.extended_tweet["full_text"]
            except AttributeError:
                tweet = status.text
            #words = tweet.split()
            for tag in self.tags:
                if tag.upper() in tweet.upper():
                    self.dict_num_tweets[tag] += 1
                    for pos_word in positive_words:
                        if pos_word.upper() in tweet.upper():
                            self.dict_sentiment[tag] += 1
                            tweet_score += 1
                            break
                    for neg_word in negative_words:
                        if neg_word.upper() in tweet.upper():
                            self.dict_sentiment[tag] -= 1
                            tweet_score -= 1
                            break
                    if self.dict_sentiment[tag] < 0:
                        self.dict_pos_tweets[tag] = self.dict_num_tweets[tag] + self.dict_sentiment[tag]
                    #csv_output = csv.writer(f_output)
                    #row.append(tag)
                    #if tweet_score > 0:
                        #word = pos_word
                    #elif tweet_score < 0:
                        #word = neg_word
                    #else:
                        #word = " "
                    #row.append(word)
                    #row.append(tweet_score)
                    #row.append(status.author.screen_name)
                    #row.append(status.source)
                    #row.append(tweet)
                    #csv_output.writerow(row)
                    #row = []
                    #tweet_score = 0
                self.dict_tweet_rate[tag] = round(self.dict_num_tweets[tag] / elapsed_time.seconds * 60)
                self.dict_pos_tweet_rate[tag] = int(self.dict_pos_tweets[tag] / elapsed_time.seconds * 60)
                if tag == "trump":
                    gauge_elapsed_time = datetime.datetime.now() - self.last_gauge_time 
                    if gauge_elapsed_time.seconds > 5:
                        self.last_gauge_time = datetime.datetime.now()
                        self.current_position_1 = move_stepper_1(self.dict_pos_tweet_rate[tag], self.current_position_1)
                if tag == "biden":
                    gauge_elapsed_time = datetime.datetime.now() - self.last_gauge_time 
                    if gauge_elapsed_time.seconds > 5:
                        self.last_gauge_time = datetime.datetime.now()
                        self.current_position_2 = move_stepper_2(self.dict_pos_tweet_rate[tag], self.current_position_2)
            for tag in self.tags:
                if self.dict_num_tweets[tag] != 0:
                    sentiment_pct = round(self.dict_sentiment[tag] / self.dict_num_tweets[tag], 2)
                else:
                    sentiment_pct = 0
                message = (
                    message + tag + ": " + str(self.dict_num_tweets[tag])
                    + " / " + str(sentiment_pct)
                    + " / " + str(self.dict_pos_tweet_rate[tag])
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


def main():
    try:
        args = get_arguments()
        tags = args.keywords
        get_trends(args)
        # Start the tweepy SteamListner as asynchronous thread.
        myStreamListener = MyStreamListener(tags)
        myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener, tweet_mode='extended')
        print(" ")
        #myStream.filter(track=tags, is_async=True)
        myStream.filter(track=tags)
    except KeyboardInterrupt:
        print(" ")
        print("End by Ctrl-C")
        myStream.disconnect()
        exit()


if __name__ == "__main__":
    main()