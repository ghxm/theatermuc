import utils
import re

resi_locations = ['Marstall', 'Residenztheater', 'Cuvilliéstheater', 'Zur Schönen Aussicht']

tz = 'Europe/Berlin'
venue = 'Residenztheater'
short_id = 'resi'

current_year = utils.get_current_year()

base_url = 'https://www.residenztheater.de'

program_html = utils.get_html('https://www.residenztheater.de/spielplan')

program_bs = utils.make_soup(program_html)

event_days = program_bs.find_all('section', {'class': 'schedule__day'})

schedule_events = []

for day in event_days:

    # find events for day
    events = day.find_all(class_ = 'schedule-act')

    # find date
    for event in events:

        try:
            date = day.find(class_='schedule-act__date').get_text().strip()

            # remove weekday
            date = re.sub(r'^[A-Za-z]{2,3}\s', '', date)

            month = re.findall(r'[A-Za-z]{3,}', date)

            if len(month) > 0:
                month = month[0]
                month_num = utils.german_month_to_num(month)
                date = re.sub(r'\s*'+ month +'\s*', '.'+str(month_num)+'.', date) + str(utils.figure_out_year(int(month_num)))
            else:
                raise Exception('No month found')

        except:
            date = None

        # find time
        try:
            info = event.find(class_='schedule-act__details').get_text().strip()
        except:
            info = None

        try:
            # check if any location is mentioned
            for location in resi_locations:
                if location.lower() in info.lower():
                    break
                else:
                    location = None
        except:
            location = None

        if info is not None:
            time_match = re.findall(r'(–*\s*[0-9]{1,2}\.[0-9]{1,2}\s*)', info)


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

        # find title
        try:
            title = event.find(class_='schedule-act__title').get_text().strip()
        except:
            title = None

        # find description
        try:
            description = event.find(class_='schedule-act__author').get_text().strip()

            if event.find(class_='schedule-act__short-description') is not None:
                description = description + '. ' + event.find(class_='schedule-act__short-description').get_text().strip() + '.'
        except:
            description = None


        # find urls
        urls_dict = {}

        try:
            urls_dict['ticket'] = event.find(class_='schedule-act__cards-info').find('a')['href']
        except:
            pass


        slug = None
        try:
            slug = event.find(class_='schedule-act__title').find('a')['href']
            urls_dict['info'] = base_url + slug
        except:
            pass

        try:
            for a in event.find(class_='schedule-act__date-links').find_all('a'):
                if a.get('href') is not None and 'ics' in a['href']:
                    urls_dict['ics'] = base_url + a['href']
        except:
            pass


        # add to schedule_events
        schedule_events.append({'date': utils.ymd_string(date),
                                'year': utils.get_year(date),
                                'kw': utils.get_weeknum(date),
                                'venue': venue,
                                'slug': slug,
                                'title': title,
                                'tags': None,
                                'urls': urls_dict,
                                'time': ''.join([t.strip() for t in time_match]) if time_match is not None and len(time_match) > 0 else None,
                                'cost': None, # TODO: add cost
                                'start_datetime': start_datetime.isoformat() if start_datetime is not None else None,
                                'end_datetime': end_datetime.isoformat() if end_datetime is not None else None,
                                'location': location,
                                'description': description})


# write to file
utils.write_json(schedule_events, 'residenztheater_schedule.json')