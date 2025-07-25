import jinja2
import utils
import os
import json
import sys
from datetime import datetime
import pytz

site_title = 'theater.mucnoise.com'


schedules_dir = 'data/'
schedule_filename = 'schedule.json'
schedule_path = utils.path_to_data_folder(schedule_filename)

# Check if --skip-scrapers flag is passed
skip_scrapers = '--skip-scrapers' in sys.argv

# if there are no files in the data folder and not skipping scrapers, run all scrapers
if not skip_scrapers and len([f for f in os.listdir(utils.path_to_data_folder()) if f.endswith('json')]) == 0:

    log = utils.run_all_scrapers()

    utils.write_json(log, 'site/log.json')

else:
    try:
        log = json.load(open('site/log.json', 'r'))
    except:
        log = {'success': [], 'errors': [], 'dev': False}


if len(log['errors']) > 0:
    print('There were errors running the scrapers:')
    print(log['errors'])


utils.combine_schedules(schedules_dir, schedule_filename)


# Create a Jinja2 environment
env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'), extensions=['jinja2.ext.loopcontrols'])

# Load a template
template = env.get_template('index.j2')

# read in schedule
schedule_str = open(schedule_path, 'r').read()

schedule = json.loads(schedule_str)

try:
    utils.write_ics(schedule, 'site/schedule.ics')
except Exception as e:
    print('Error writing ics file:')
    print(e)

try:
    utils.write_json(schedule, 'site/schedule.json')
except Exception as e:
    print('Error writing json file:')
    print(e)

schedule = utils.remove_past_events(schedule)


# aggregate schedule by day
schedule = utils.aggregate_schedule(schedule, groups=['year','kw','date', 'venue'])

# make start_datetime and end_datetime into datetime objects
for year in schedule.keys():
    for kw in schedule[year].keys():
        for date in schedule[year][kw].keys():
            for venue in schedule[year][kw][date].keys():
                for event in schedule[year][kw][date][venue]:
                    event['date_datetime'] = utils.make_date(event['date'], 'Europe/Berlin') if event['date'] is not None else None
                    event['start_datetime'] = utils.ensure_tz(datetime.fromisoformat(event['start_datetime'])) if event['start_datetime'] is not None else None
                    event['end_datetime'] = utils.ensure_tz(datetime.fromisoformat(event['end_datetime'])) if event['end_datetime'] is not None else None

# get a dict of date-weekdays
## get all dates
dates = []
for year in schedule.keys():
    for kw in schedule[year].keys():
        for date in schedule[year][kw].keys():
            dates.append(date)

date_weekdays = {date: utils.get_weekday(date) for date in dates}

tz = pytz.timezone('Europe/Berlin')


# sort schedule by date
for year in schedule.keys():
    for kw in schedule[year].keys():
        for date in schedule[year][kw].keys():
            for venue in schedule[year][kw][date].keys():
                schedule[year][kw][date][venue] = sorted(schedule[year][kw][date][venue], key=lambda k: k['start_datetime'] if k['start_datetime'] is not None else datetime.now(tz))

def path_exists(path):
    return os.path.exists(path)




# Write the rendered template to a file
with open('site/index.html', 'w') as f:
    f.write(template.render(site_title=site_title,schedule=schedule, date_weekdays=date_weekdays, today = utils.get_today(), today_datetime = utils.get_today(dt=True), now = datetime.now(tz), log = log, path_exists = path_exists))

