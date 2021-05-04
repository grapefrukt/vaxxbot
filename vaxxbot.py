import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from dateutil.parser import parse
import locale

newline = '\n'
target_dose_count = 8189892*2

class VaxDay :
    def __init__(self, date, count): 
        self.date = date
        self.count = count

def make_ordinal(n):
    n = str(n)
    if (n != "11" and n != "12") and (n[-1] == "1" or n[-1] == "2") :
        suffix = 'a'
    else :
        suffix = 'e'
    
    return str(n) + suffix


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
    message += f"en ökning med {(delta_count/target_dose_count*100):.2f} procentenheter sen senaste uppdateringen."

    return message

try :
    with open('cache.txt', 'r') as file:
        most_recent_date = parse(file.read())
except OSError :
    most_recent_date = parse("1970-01-01")

url = 'https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/statistik-och-analyser/statistik-over-registrerade-vaccinationer-covid-19/'
requests.get(url)
page = requests.get(url)

soup = BeautifulSoup(page.text, 'lxml')

table_caption = soup.find('caption', string = 'Tabell 1. Antal rapporterade vaccinationer totalt')
table_body = table_caption.find_parent('table').find('tbody')

collection = []

for j in reversed(table_body.find_all('tr')) :
    row_data = j.find_all('td')
    #print(row_data[0].text, row_data[1].text)
    
    day = VaxDay(
        date = parse(row_data[0].text), 
        count = int("".join(row_data[1].text.split()))
    )
    collection.append(day)

locale.setlocale(locale.LC_ALL, 'sv_SE.utf8')

last_entry = None
for entry in collection :
    if not last_entry is None: print(make_message(last_entry, entry))
    print("")
    last_entry = entry

# message = 

if last_entry.date > most_recent_date :
    print("time to go!")
else :
    print("last timestamp was same as retrieved, no go")

with open("cache.txt", "w") as file:
    print(f"{last_entry.date:%Y-%m-%d}", file=file)