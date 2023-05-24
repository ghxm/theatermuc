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


def get_events(month, driver):

    import utils

    program_html = utils.get_html_selenium(f'https://www.staatsoper.de/spielplan/{month}', driver)

    program_bs = utils.make_soup(program_html)

    event_days = program_bs.find_all(class_ = 'activity-group')

    return event_days

none_count = 0
event_days = []

driver = utils.get_selenium_driver()

# get all year-month values
for year in range(current_year, current_year + 2):
    for month in range(current_month, 13):

        month = str(month).zfill(2)

        # wait 1-8 seconds
        time.sleep(random.randint(1, 8))

        events_month = get_events(f'{year}-{month}', driver)

        event_days.extend(events_month)

        if len(events_month) == 0:
            none_count += 1
        elif none_count > 3:
            break
        else:
            none_count = 0

# close driver
driver.close()


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
            title = event.find(class_='activity-list__text').find(re.compile(r'h[0-9]')).get_text().strip()
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





# write to file
utils.write_json(schedule_events, 'staatsoper_schedule.json')