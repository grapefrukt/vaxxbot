import configparser
import tweepy

config = configparser.ConfigParser()
config.read('vaxxbot.cfg')
config = config['vaxxbot']

# Authenticate to Twitter
# auth.set_access_token(config["access_token"], config["access_token_secret"])

auth = tweepy.OAuthHandler(config["api_key"], config["api_secret_key"])

# get access token from the user and redirect to auth URL
auth_url = auth.get_authorization_url()
print('Authorization URL: ' + auth_url)

# ask user to verify the PIN generated in broswer
verifier = input('PIN: ').strip()
auth.get_access_token(verifier)
print('ACCESS_KEY = "%s"' % auth.access_token)
print('ACCESS_SECRET = "%s"' % auth.access_token_secret)

# authenticate and retrieve user name
auth.set_access_token(auth.access_token, auth.access_token_secret)
api = tweepy.API(auth)
username = api.me().name
print('Ready to post to ' + username)