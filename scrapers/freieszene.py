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

# fetch events in 10-day increments for the next 18 months
max_iterations = 55  # ~550 days, about 18 months
for i in range(max_iterations):
    date_str = utils.ymd_string(date_today)
    events_month = get_events(date_str)

    print(f'Iteration {i+1}: {date_str} - found {len(events_month)} events')

    # advance by 10 days
    date_today = date_today + timedelta(days=10)

    events.extend(events_month)

    if len(events_month) == 0:
        none_count += 1
        # stop if we have 10 consecutive empty periods (100 days with no events)
        if none_count >= 10:
            print(f'Stopping after {none_count} consecutive empty periods')
            break
    else:
        none_count = 0

events = list({v.uid:v for v in events}.values())

schedule_events = []

for event in events:

    if event.all_day:
        all_day = True
    else:
        all_day = False

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

    if end_datetime == start_datetime:
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
        print('No date found for event: ' + str(event.name))
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

        if location is not None:
            loc_match = re.search(location.lower() + r':\s*', title.lower())

            if loc_match:
                title = title[loc_match.end():]

        if title.lower().startswith('hofspielhaus:'):
            title = title[13:]

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
                            'start_datetime': start_datetime.isoformat() if start_datetime is not None and not all_day else None ,
                            'end_datetime': end_datetime.isoformat() if end_datetime is not None and not all_day else None ,
                            'location': location,
                            'description': description})



# write to file
utils.write_json(schedule_events, 'freieszene_schedule.json')