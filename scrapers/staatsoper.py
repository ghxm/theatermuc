import utils
import re
import random
import time


tz = 'Europe/Berlin'
venue = 'Bayerische Staatsoper'
short_id = 'bso'

current_year = utils.get_current_year()
current_month = utils.get_current_month()

base_url = 'https://www.staatsoper.de'
spielplan_url = base_url + '/spielplan'

# number of months to scrape, starting with the current one
months_ahead = 18

error = None

def get_events(month, driver):
    """
    Fetch one month from the calendar's ajax endpoint.

    The /spielplan/{month} page itself is only the shell and always renders the
    same default month, so the month has to come from activities.ajax.
    """

    global error

    import utils

    try:
        program_html = utils.get_html_selenium(f'{spielplan_url}/{month}/activities.ajax', driver)
    except Exception as e:
        error = e
        print(e)
        return []

    program_bs = utils.make_soup(program_html)

    event_days = program_bs.find_all(class_ = 'activity-group')

    return event_days

event_days = []

driver = utils.get_selenium_driver()

# load the schedule page once, so the ajax endpoint is requested in session
utils.get_html_selenium(spielplan_url, driver)

months_with_events = 0

for i in range(months_ahead):

    month_index = current_month - 1 + i
    year = current_year + month_index // 12
    month = str(month_index % 12 + 1).zfill(2)

    # wait 1-5 seconds
    time.sleep(random.randint(1, 5))

    events_month = get_events(f'{year}-{month}', driver)

    # months without events are normal (the house is closed over the summer)
    if len(events_month) > 0:
        months_with_events += 1

    event_days.extend(events_month)

print(f'{months_with_events} of {months_ahead} months returned events')

# close driver
driver.quit()


schedule_events = []

for day in event_days:

    # find events for day
    events = day.find_all(class_ = 'activity-list__row')

    # find date
    for event in events:

        try:
            date = event['data-date']


        except:
            date = None

        # find time
        try:
            info = event.find(class_='activity-list__text').find('span').get_text().strip()
        except:
            info = None

        try:
            # check if any location is mentioned
            time_location = info.split(' | ', 1)
        except:
            time_location = None

        if time_location is not None:
            try:
                time = time_location[0]
            except:
                time = None

            try:
                location = time_location[1]
            except:
                location = None


        if time is not None:

            time_match = re.findall(r'(–*\s*[0-9]{1,2}\.[0-9]{1,2}\s*)', info)

        if time_match is not None:

            start_time = time_match[0].strip().replace('.', ':')

            try:
                end_time = time_match[1].replace('–', '').strip().replace('.', ':')
            except:
                end_time = None


        try:
            # make datetime
            start_datetime = utils.make_datetime(date, start_time, tz)
        except:
            start_datetime = None

        try:
            # make datetime
            end_datetime = utils.make_datetime(date, end_time, tz)
        except:
            end_datetime = None

        # find title
        try:
            title = event.find(class_='activity-list__text').find(class_='h3').get_text().strip()
        except:
            title = None

        # find description
        try:
            description = event.find(class_='activity-list--toggle__content').find('p').get_text().strip()
        except:
            description = None

        # find price
        prices_dict = {}
        try:
            prices_dict['info'] = event.find(class_='activity-list-price-info').get_text().strip()
        except:
            pass

        # find urls
        urls_dict = {}

        try:
            urls_dict['ticket'] = event.find(class_='button--ticket')['href']
        except:
            pass


        slug = None
        try:
            slug = event.find('a', class_='activity-list__content')['href']
            urls_dict['info'] = base_url + slug
        except:
            pass

        try:
           urls_dict['ics'] = base_url + event.find(class_='button-save-date')['href']
        except:
            pass

        # TAGS

        tags = []
        try:
            tag = event.find(class_='activity-list__channel').get_text().strip()
            tags = [tag]
        except:
            pass

        if date is None:
            print('No date found for event: ' + title)
            continue

        # add to schedule_events
        schedule_events.append({'date': utils.ymd_string(date) if date is not None else None,
                                'year': utils.get_year(date),
                                'kw': utils.get_weeknum(date),
                                'venue': venue,
                                'slug': slug,
                                'title': title,
                                'tags': tags,
                                'urls': urls_dict,
                                'time': ''.join([t.strip() for t in time_match]) if time_match is not None and len(time_match) > 0 else None,
                                'cost': prices_dict, # TODO: add cost
                                'start_datetime': start_datetime.isoformat() if start_datetime is not None else None,
                                'end_datetime': end_datetime.isoformat() if end_datetime is not None else None,
                                'location': location,
                                'description': description})





# deduplicate events: the /spielplan/{year-month} page returns the full
# program regardless of the requested month, so the same event is collected
# once per month-request. Use the unique slug as the dedup key, falling back
# to (title, start_datetime, location) when no slug is available.
seen = set()
deduped_events = []
for event in schedule_events:
    key = event['slug'] if event['slug'] is not None else (event['title'], event['start_datetime'], event['location'])
    if key in seen:
        continue
    seen.add(key)
    deduped_events.append(event)

schedule_events = deduped_events

print(f'Total events found: {len(schedule_events)}')

# write to file
utils.write_json(schedule_events, 'staatsoper_schedule.json')

# scraping nothing at all means the site blocked us, so fail instead of
# quietly publishing an empty schedule
if len(schedule_events) == 0:
    if error is not None:
        raise error
    raise Exception('No events found, staatsoper likely blocked the scraper')