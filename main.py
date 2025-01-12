import time

import schedule

from OLXParser import OLXParser
from db import OLXAdsDatabase

db = OLXAdsDatabase()

def parse_website():
    parser = OLXParser(db)
    parser.parse(pages=5)

schedule.every(1).minutes.do(parse_website)
schedule.every().day.at("12:00").do(db.create_dump)

while True:
    schedule.run_pending()
    time.sleep(1)
