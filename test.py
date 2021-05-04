import configparser
import tweepy

config = configparser.ConfigParser()
config.read('vaxxbot.cfg')
config = config['vaxxbot']

# Authenticate to Twitter
auth = tweepy.OAuthHandler(config["api_key"], config["api_secret_key"])
auth.set_access_token(config["access_token"], config["access_token_secret"])

# Create API object
api = tweepy.API(auth)

# Create a tweet
api.update_status("Hello Tweepy")