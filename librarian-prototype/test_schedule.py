# test schedule at("time" ) order
# question: if at("time") has already passed when job is scheduled, is it run
# right away or not?
#
import schedule
from time import sleep
from datetime import datetime

def job(n):
    print('Running job', n, 'at', datetime.now().isoformat())

schedule.every().day.at("22:38").do(job, 1)
schedule.every().day.at("22:55").do(job, 2)
schedule.every().day.at("22:56").do(job, 3)

while True:
    schedule.run_pending()
    sleep(1)
