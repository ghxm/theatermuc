import re

import utils

program_html = utils.get_html('https://www.muenchner-volkstheater.de/programm/spielplan')

program_bs = utils.make_soup(program_html)

event_days = program_bs.find_all(class_="schedule--day-wrapper")

schedule_events = []

venue = 'Volkstheater'
tz = 'Europe/Berlin'
short_id = 'vt'
base_url = 'https://www.muenchner-volkstheater.de'

for event_day in event_days:

    # figure out date
    try:
        date_day = event_day.find(class_="schedule--day").get_text().strip()
    except:
        print('Could not find date_day')
        continue

    try:
        date_month = event_day.find_parent(class_="schedule--month-wrapper").find(class_='schedule--month-title').get_text().strip()
        date_month = utils.german_month_to_num(date_month)
    except:
        print('Could not find date_month')
        continue

    try:
        date_year = utils.figure_out_year(date_month)
    except:
        print('Could not find date_year')
        continue

    date = str(date_year) + '-' + str(date_month) + '-' + str(date_day)

    events = event_day.find_all(class_="schedule--day-content")

    for event in events:

        # EVENT TIME
        try:
            event_time = event.find(class_="field-event-time").get_text().strip()
        except:
            event_time = None

        time_match = []
        start_time = None
        end_time = None

        if event_time is not None:
            time_match = re.findall(r'(–*\s*[0-9]{1,2}:[0-9]{1,2}\s*)', event_time)

            if len(time_match) > 0:
                start_time = time_match[0].strip().replace('.', ':')

                try:
                    end_time = time_match[1].replace('–', '').strip().replace('.', ':')
                except:
                    end_time = None

        start_datetime = None
        end_datetime = None

        try:
            # make datetime
            start_datetime = utils.make_datetime(date, start_time, tz)
        except:
            pass

        try:
            # make datetime
            end_datetime = utils.make_datetime(date, end_time, tz)
        except:
            pass

        # EVENT LOCATION
        try:
            location = event.find(class_="field-event-location").get_text().strip()
        except:
            location = None

        # EVENT TITLE

        try:
            title_element = event.find(class_="schedule--title")
            title = title_element.get_text().strip()
        except:
            title = None

        # EVENT SLUG
        try:
            slug = title_element.find('a')['href']
        except:
            slug = None

        # EVENT TAGS
        try:
            tags = event.find_all(class_='schedule--title-post')
            tags = [tag.get_text().strip() for tag in tags]
        except:
            tags = None

        # EVENT URLS

        urls_dict = {'other': []}

        try:
            urls_dict['info'] = base_url + slug
        except:
            urls_dict['info'] = base_url + slug

        try:
            urls_dict['ticket'] = event.find(class_='schedule--tickets-link')['href']
        except:
            urls_dict['ticket'] = None

        # EVENT DESCRIPTION
        try:
            description = event.find(class_="field-subtitle-event-notes").get_text().strip()
        except:
            description = ''

        try:
            description = event.find(class_="field-event-author-director").get_text().strip() + '. ' + description + '.'
        except:
            pass

        if description == '':
            description = None



        # add to schedule_events
        schedule_events.append({'date': utils.ymd_string(date),
                                'year': utils.get_year(date),
                                'kw': utils.get_weeknum(date),
                                'venue': venue,
                                'slug': slug,
                                'title': title,
                                'tags': tags,
                                'urls': urls_dict,
                                'time': event_time,
                                'cost': None, # TODO: add cost
                                'start_datetime': start_datetime.isoformat() if start_datetime is not None else None,
                                'end_datetime': end_datetime.isoformat() if end_datetime is not None else None,
                                'location': location,
                                'description': description})

# write out to json
utils.write_json(schedule_events, 'volkstheater_schedule.json')




