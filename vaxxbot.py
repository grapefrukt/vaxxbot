import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from dateutil.parser import parse
import locale
import configparser
import tweepy

# first we set the locale to swedish
locale.setlocale(locale.LC_ALL, 'sv_SE')

# parse the config file, mainly has twitter authentication bits
config = configparser.ConfigParser()
config.read('vaxxbot.cfg')
config = config['vaxxbot']

target_dose_count = int(config['target_dose_count'])

# a lil' data structure for storing things
class VaxDay :
    def __init__(self, date, count): 
        self.date = date
        self.count = count

# utility function to format dates nicely
def make_ordinal(n):
    n = str(n)
    if (n != "11" and n != "12") and (n[-1] == "1" or n[-1] == "2") :
        suffix = 'a'
    else :
        suffix = 'e'
    
    return str(n) + suffix

# this function assembles the actual message, two variants depending on if it's a single or multi day update
def make_message(previous_day, day) :
    delta_count = day.count - previous_day.count if previous_day else 1
    delta_days = (day.date - previous_day.date).days if previous_day else 1
    count_per_day = round(delta_count / delta_days)

    message = ""

    if delta_days > 1 :
        message += f"den {make_ordinal(day.date.day)} {day.date:%B} rapporterades {delta_count:n} nya vaccindoser, "
        message += f"{count_per_day:n} doser om dagen över {delta_days} dagar. "
    else :
        message += f"den {make_ordinal(day.date.day)} {day.date:%B} rapporterades {delta_count:n} nya vaccindoser sedan gårdagen. "
    
    message += f"totalt har {day.count:n} doser getts, "
    message += f"vilket motsvarar {(day.count/target_dose_count*100):.1f}% av det totala antalet doser som ska ges till alla vuxna, "
    message += f"en ökning med {(delta_count/target_dose_count*100):.2f} procentenheter sedan senaste uppdateringen."

    return message

# try to read the text file with the date of the last update
try :
    with open('cache.txt', 'r') as file:
        last_update_date = parse(file.read()).date()
except :
    last_update_date = parse("1970-01-01").date()

# figure out current time
current_time = datetime.datetime.now()
print(f"current date/time: {current_time:%Y-%m-%d %H:%M}")

# figure out how long it's been since we last posted
last_update_delta = current_time.date() - last_update_date

# now, we start to try and early out for a number of reasons

# first, if we already posted today, we're done already
if last_update_delta.days == 0 : 
    print("already posted today")
    quit()
else :
    print(f"{last_update_delta.days} day(s) since last post")

# if it's not an "update day" (tuesday to friday), we can bail
if not 1 <= current_time.weekday() <= 4 :
    print(f"no updates on this weekday ({current_time.weekday()})")
    quit()

# if it's before the stated update time (14:00) we can wait some more
if current_time.hour < 14 :
    print(f"too early in the day for updates (hour is {current_time.hour})")
    quit()


# if all those checks pass, we go to the server for data

print('fetching data from server...')
url = 'https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/statistik-och-analyser/statistik-over-registrerade-vaccinationer-covid-19/'
requests.get(url)
page = requests.get(url)
soup = BeautifulSoup(page.text, 'lxml')

table_caption = soup.find('caption', string = 'Tabell 1. Antal rapporterade vaccinationer totalt.')
table_body = table_caption.find_parent('table').find('tbody')

# once that's loaded and parsed, we try to pick out what we need
collection = []
for j in reversed(table_body.find_all('tr')) :
    row_data = j.find_all('td')
    
    day = VaxDay(
        date = parse(row_data[0].text).date(), 
        count = int("".join(row_data[1].text.split()))
    )
    collection.append(day)

# look at the last item in the list, if it's the same date (or older) than when we last posted, bail
if collection[-1].date <= last_update_date :
    print(f"no new data since last post ({last_update_date}), quitting...")
    quit()


# then, we tweet
print('sending tweet...')
message = make_message(collection[-2], collection[-1])

# Authenticate to Twitter
auth = tweepy.OAuthHandler(config["api_key"], config["api_secret_key"])
auth.set_access_token(config["access_token"], config["access_token_secret"])

# Create API object
api = tweepy.API(auth)

# Create a tweet
api.update_status(message)

# finally, write the new most recent date to the cache
print('updating cache...')
with open("cache.txt", "w") as file:
    print(f"{collection[-1].date:%Y-%m-%d}", file=file)

print("all done")