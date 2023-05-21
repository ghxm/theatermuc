import jinja2
import utils
import os
import json
from datetime import datetime
import pytz

site_title = 'Theater Munich'


schedules_dir = 'data/'
schedule_filename = 'schedule.json'
schedule_path = utils.path_to_data_folder(schedule_filename)


log = utils.run_all_scrapers()

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
    utils.write_ics(schedule, 'site/static/schedule.ics')
except Exception as e:
    print('Error writing ics file:')
    print(e)

try:
    utils.write_json(schedule, 'site/static/schedule.json')
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
                    event['start_datetime'] = datetime.fromisoformat(event['start_datetime']) if event['start_datetime'] is not None else None
                    event['end_datetime'] = datetime.fromisoformat(event['end_datetime']) if event['end_datetime'] is not None else None

# get a dict of date-weekdays
## get all dates
dates = []
for year in schedule.keys():
    for kw in schedule[year].keys():
        for date in schedule[year][kw].keys():
            dates.append(date)

date_weekdays = {date: utils.get_weekday(date) for date in dates}

def path_exists(path):
    return os.path.exists(path)

tz = pytz.timezone('Europe/Berlin')


# Write the rendered template to a file
with open('site/index.html', 'w') as f:
    f.write(template.render(site_title=site_title,schedule=schedule, date_weekdays=date_weekdays, today = utils.get_today(), today_datetime = utils.get_today(dt=True), now = datetime.now(tz), log = log, path_exists = path_exists))

