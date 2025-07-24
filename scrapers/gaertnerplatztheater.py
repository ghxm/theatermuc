import utils
import re


tz = 'Europe/Berlin'
venue = 'Gärtnerplatztheater'
short_id = 'gtp'

current_year = utils.get_current_year()

base_url = 'https://www.gaertnerplatztheater.de/'


def get_events(month):

    import utils
    import re

    program_html = utils.get_html(f'https://www.gaertnerplatztheater.de/de/spielplan/{month}.html')

    program_bs = utils.make_soup(program_html)

    event_days = [d for d in program_bs.find_all(class_='tag clearfix')]

    for day in event_days:
        day['data-month-code'] = month


    return event_days


# get all month values
program_html = utils.get_html('https://www.gaertnerplatztheater.de/de/spielplan/index.html')

program_bs = utils.make_soup(program_html)

months = [o.get_text().replace(' ', '-').lower() for o in program_bs.find(id='filter-date').find_all('option') if re.search(r'[0-9]', o.get_text()) is not None]

event_days = []

for month in months:
    event_days += get_events(month)


schedule_events = []

for day in event_days:

    try:
        month, year = day['data-month-code'].split('-')

        month = utils.german_month_to_num(month)


    except Exception as e:
        month = None
        year = None

    # find events for day
    events = day.find_all(class_ = 'performance')

    # find date
    for event in events:

        try:
            day_num = day.find(class_='day').get_text().strip()
        except:
            try:
                day_num = day.find_previous(class_='anchor')['name'].replace('a_', '')
            except:
                day_num = None

        try:

            date = f'{day_num}.{month}.{year}'

        except:
            date = None

        # find time
        try:
            time = event.find(class_='time').get_text().strip()
        except:
            time = None

        if time is not None:
            time_match = re.findall(r'(–*\s*[0-9]{1,2}\.[0-9]{1,2}\s*)', time)


        if len(time_match) > 0:
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

        try:
            location = event.find(class_='location').get_text().strip()
        except:
            location = None

        # find title
        try:
            title = event.find(class_='title').find(re.compile(r'h[0-9]')).get_text().strip()
        except:
            title = None

        # find description
        try:
            tags = [event.find(class_='title').find('p').get_text().strip()]

        except:
            tags = []

        try:
            description += event.find(class_='teaserText').get_text().strip()
        except:
            description = None


        # find urls
        urls_dict = {}

        try:
            urls_dict['ticket'] = event.find(class_='ticketLink').find('a')['href']
        except:
            pass


        slug = None
        try:
            slug = event.find(class_='title').find(re.compile(r'h[0-9]')).find('a')['href']
            slug = slug.replace('./', 'de/', 1)
            urls_dict['info'] = base_url + slug
        except:
            pass

        try:
            urls_dict['ics'] = event.find(class_='icalLink').find('a')['href']
        except:
            pass

        # find price
        prices_dict = {}
        try:
            prices_dict['info'] = event.find(class_='preise').get_text().strip()
        except:
            pass

        if date is None:
            print('No date found for event: ' + str(title))
            continue

        # add to schedule_events
        schedule_events.append({'date': utils.ymd_string(date) if date is not None else None,
                                'year': utils.get_year(date),
                                'kw': utils.get_weeknum(date),
                                'venue': venue,
                                'slug': slug,
                                'title': title.title() if title is not None else None,
                                'tags': None,
                                'urls': urls_dict,
                                'time': ''.join([t.strip() for t in time_match]) if time_match is not None and len(time_match) > 0 else None,
                                'cost': prices_dict, # TODO: add cost
                                'start_datetime': start_datetime.isoformat() if start_datetime is not None else None,
                                'end_datetime': end_datetime.isoformat() if end_datetime is not None else None,
                                'location': location,
                                'description': description})





# write to file
utils.write_json(schedule_events, 'gaertnerplatztheater_schedule.json')