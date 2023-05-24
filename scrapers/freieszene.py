import utils
import re
import random
import time
from datetime import datetime, timedelta

tz = 'Europe/Berlin'
venue = 'Freie Szene'
short_id = 'free'

current_year = utils.get_current_year()
current_month = utils.get_current_month()

base_url = 'https://www.freieszenemuc.de'


def get_events(date):

    import utils

    program_ics = utils.get_html(f'https://www.freieszenemuc.de/?post_type=tribe_events&tribe-bar-date={date}&ical=1&eventDisplay=list')

    cals = utils.parse_ics(program_ics)

    events = []

    for cal in cals:
        try:
            events.extend(cal.events)
        except:
            pass

    return events


none_count = 0
events = []

# get today's date

date_today = utils.get_today(dt=True)


# get all year-month values
for year in range(current_year, current_year + 2):
    for month in range(current_month, 13):

        month = str(month).zfill(2)

        events_month = get_events(utils.ymd_string(date_today))

        # add 25 days to date_today
        date_today = date_today + timedelta(days=10)


        events.extend(events_month)

        if len(events_month) == 0:
            none_count += 1
        elif none_count > 3:
            break
        else:
            none_count = 0

events = list({v.uid:v for v in events}.values())

schedule_events = []

for event in events:

    if event.all_day:
        all_day = True

    try:
        # make datetime
        start_datetime = event.begin.datetime
    except:

        start_datetime = None

    try:
        # make datetime
        end_datetime = event.end.datetime
    except:
        end_datetime = None

    try:
        date = event.begin.date()
    except:
        date = None



    # find description
    try:
        description = event.description
    except:
        description = None

    # @TODO find price


    # find urls
    urls_dict = {}

    try:
        urls_dict['info'] = event.url
    except:
        pass


    slug = None

    try:
        slug = event.url.replace(base_url, '')

    except:
        pass


    # TAGS

    tags = []
    try:
        tags = list(event.categories)
    except:
        pass

    if date is None:
        print('No date found for event: ' + title)
        continue

    # location
    location = None

    try:
        location = event.location

        location = re.sub(r',.*', '', location)

    except:
        pass

    # find title
    try:
        title = event.name

        title = re.sub(location + r':\s*', '', title)
    except:
        title = None

    # add to schedule_events
    schedule_events.append({'date': utils.ymd_string(date) if date is not None else None,
                            'year': utils.get_year(date),
                            'kw': utils.get_weeknum(date),
                            'venue': venue,
                            'slug': slug,
                            'title': title,
                            'tags': tags,
                            'urls': urls_dict,
                            'time': None,
                            'cost': None, # TODO: add cost
                            'start_datetime': start_datetime.isoformat() if start_datetime is not None else None,
                            'end_datetime': end_datetime.isoformat() if end_datetime is not None else None,
                            'location': location,
                            'description': description})



schedule_events = list(set(schedule_events))

# write to file
utils.write_json(schedule_events, 'freieszene_schedule.json')