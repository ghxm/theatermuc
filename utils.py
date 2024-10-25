import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, date
import pytz
import os
import itertools
from collections import defaultdict
from ics import Calendar, Event
from seleniumbase import Driver
import backoff
import certifi

@backoff.on_exception(backoff.expo, requests.ConnectTimeout, max_value=32)
def get_html(url):
    """
    Get html from url.
    """

    # add header
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36; ghxm.github.io/theatermuc/ data collection'}


    # allow cookies
    s = requests.Session()


    r = s.get(url, headers=headers, verify=False)
    r.raise_for_status()

    return r.text


def get_selenium_driver():

    driver = Driver(browser="chrome", uc=True, headless=False)

    return driver

def get_html_selenium(url, driver = None):
    """
    Get html from url using selenium.
    """

    if driver is None:
        driver = get_selenium_driver()

    # add timeout
    driver.set_page_load_timeout(30)

    driver.get(url)

    html = driver.page_source

    return html

def make_soup(html):
    """
    Make soup from html.
    """

    soup = BeautifulSoup(html, 'html.parser')

    return soup

def write_json(data, filename):
    """
    Write data to json file.
    """

    if '/' not in filename:
        path = os.path.join(path_to_data_folder(), filename)
    else:
        path = filename

    with open(path, 'w') as f:
        json.dump(data, f)

def make_datetime(date, time, tz):
    """
    Make datetime object from date and time.
    """

    datetime_str = date + " " + time

    # create new date object

    # check date format (DD.MM.YYYY or YYYY-MM-DD)
    if len(date.split('.')) == 3:

        # format: DD.MM.YYYY
        format = "%d.%m.%Y %H:%M"

    else:

        # format: YYYY-MM-DD
        format = "%Y-%m-%d %H:%M"

    datetime_obj = datetime.strptime(datetime_str, format)


    # set timezone
    tz = pytz.timezone(tz)
    datetime_obj = tz.localize(datetime_obj)

    return datetime_obj

def make_date(date, tz):
    result = make_datetime(date, '00:00', tz)

    return result.date()

def ensure_tz(dt, tz = "Europe/Berlin"):
    """
    Ensure that datetime object has timezone.
    """

    if dt.tzinfo is None:
        dt = pytz.timezone(tz).localize(dt)

    return dt


# translate a german month string to a number
def german_month_to_num(month):

    months = {'Januar': 1,
                'Februar': 2,
                'März': 3,
                'April': 4,
                'Mai': 5,
                'Juni': 6,
                'Juli': 7,
                'August': 8,
                'September': 9,
                'Oktober': 10,
                'November': 11,
                'Dezember': 12}

    # partial match / starts with
    for key in months.keys():
        if key.lower().startswith(month.lower()):
            return months[key]


def get_current_year():
    """
    Get current year.
    """

    tz = pytz.timezone('Europe/Berlin')

    now = datetime.now(tz)

    return now.year

def get_current_month():

    tz = pytz.timezone('Europe/Berlin')

    now = datetime.now(tz)

    return now.month


def figure_out_year(month):

    current_month = datetime.now().month
    current_year = get_current_year()

    if month < current_month:
        year = current_year + 1
    else:
        year = current_year

    return year


def path_to_data_folder(filename=None):
    """
    Get path to data folder.
    """

    # get path of current file
    path = os.path.dirname(os.path.realpath(__file__))

    if filename is not None:
        return os.path.join(path, 'data/', filename)
    else:

        # get path of data folder
        return os.path.join(path, 'data/')

def run_all_scrapers(dir = 'scrapers/'):

    # get list of all files in dir
    scrapers = [d for d in os.listdir(dir) if d.endswith('.py') and not d.startswith('_')]

    log = {
        'success': [],
        'errors': [],
        'dev': False}

    # loop over all scrapers
    for scraper in scrapers:

            try:
                # get path of scraper
                path = os.path.join(dir, scraper)

                print('Running scraper: ' + scraper)

                # run scraper using exec
                exec(open(path).read(), globals(), globals())

                # add scraper to success list
                log['success'].append(scraper)
            except Exception as e:
                log['errors'].append({'scraper': scraper, 'error': str(e)})
                print('Error in scraper: ' + scraper)
                print(e)

    return log



def parse_ics(ics_string):

    # parse ics string
    c = Calendar.parse_multiple(ics_string)

    return c


def combine_schedules(schedule_dir, out_filename):

    # get all schedules
    schedules = [d for d in os.listdir(schedule_dir) if d.endswith('schedule.json') and d != 'schedule.json']

    # create empty list
    all_events = []

    # loop over all schedules
    for schedule in schedules:

        # get path of schedule
        path = os.path.join(schedule_dir, schedule)

        # open schedule
        with open(path, 'r') as f:
            events = json.load(f)

        # add events to list
        all_events += events

    # write all events to json file
    write_json(all_events, out_filename)

    return all_events

def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value

def aggregate_schedule(schedule, groups = []):

    # sort by groups
    schedule.sort(key=lambda x: tuple(x[g] for g in groups))

    # group by groups
    schedule_grouped = itertools.groupby(schedule, key=lambda x: tuple(x[g] for g in groups))

    # create a dict for the aggregated schedule with the identified groups
    schedule_agg = defaultdict(dict)

    # set the events for each group(s)
    for group, events in schedule_grouped:

            nested_set(schedule_agg, group, list(events))


    return schedule_agg


def ymd_string (in_date):
    from datetime import datetime, timedelta, date

    # try to parse date
    if isinstance(in_date, str):
        try:
            out_date = datetime.strptime(in_date, '%d.%m.%Y')
        except ValueError:
            out_date = datetime.strptime(in_date, '%Y-%m-%d')
    elif isinstance(in_date, (datetime, date)):
        out_date = in_date
    else:
        raise ValueError('Date must be string or datetime object.')

    # convert to string
    out_date = out_date.strftime('%Y-%m-%d')

    return out_date

def get_weekday(date):

    if isinstance(date, str):
        date = make_datetime(date, '00:00', 'Europe/Berlin')

    return date.strftime('%A')

def get_today(dt = False, tz = 'Europe/Berlin'):

    # set timezone
    tz = pytz.timezone(tz)

    if dt:
        return datetime.now(tz).date()
    else:

        return datetime.now(tz).date().strftime('%Y-%m-%d')

def get_year(date):

    if isinstance(date, str):
        date = make_datetime(date, '00:00', 'Europe/Berlin')

    # retrun the ISO year
    return date.strftime('%G')

def get_weeknum(date):

    if isinstance(date, str):
        date = make_datetime(date, '00:00', 'Europe/Berlin')

    # retrun the ISO week number
    return date.strftime('%V')

def remove_past_events(schedule, date=get_today(dt=True)):

    # filter past events
    schedule = [event for event in schedule if make_date(event['date'], 'Europe/Berlin') >= date if event['date'] != '' and event['date'] is not None]

    return schedule

def convert_json_to_ics(schedule):

    # create calendar
    cal = Calendar()

    # loop over all events
    for event in schedule:

        try:

            # create event
            ics_event = Event()

            # set event properties
            ics_event.name = event['title']
            ics_event.begin = event['start_datetime']


            if event['end_datetime'] is not None and event['end_datetime'] < event['start_datetime']:
                # adjust date to next day
                ics_event.end = datetime.fromisoformat(event['start_datetime']) + timedelta(days=1) if event['start_datetime'] is not None else None
            else:

                ics_event.end = event['end_datetime'] if event['end_datetime'] is not None else datetime.fromisoformat(event['start_datetime']) + timedelta(hours=1) if event['start_datetime'] is not None else None

            ics_event.description = event['description'] if event['description'] is not None else ''

            ics_event.description = ics_event.description + '\n\n' + 'Info: ' + event['urls']['info'] if event['urls'].get('info') is not None else ics_event.description

            ics_event.description = ics_event.description + '\n\n' + 'Tickets: ' + event['urls']['ticket'] if event['urls'].get('ticket') is not None else ics_event.description

            try:
                ics_event.url = event['urls']['info']
            except:
                pass

            ics_event.location = event['venue']
            ics_event.location = ics_event.location + event['location'] if event['location'] is not None else ics_event.location

            # add event to calendar
            cal.events.add(ics_event)

        except Exception as e:
            print('Could not add event ' + event['title'] + ' to calendar: ' + str(e))

    return cal

def write_ics(schedule, filepath):

    # convert schedule json to ics
    ics = convert_json_to_ics(schedule)

    # write ics file
    with open(filepath, 'w') as f:
        f.write(ics.serialize())