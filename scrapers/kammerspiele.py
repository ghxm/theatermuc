import re

import utils

program_html = utils.get_html('https://www.muenchner-kammerspiele.de/de/programm/')

program_bs = utils.make_soup(program_html)

event_days = program_bs.find_all('div', {'class': 'events-group'})

schedule_events = []

venue = 'Münchner Kammerspiele'
tz = 'Europe/Berlin'
short_id = 'mk'
base_url = 'https://www.muenchner-kammerspiele.de'

for event_day in event_days:

    try:
        date = event_day['data-date']
    except:
        date = None

    events = event_day.find_all('div', {'class': 'preview-event'})

    for event in events:

        try:
            slug = event['data-href']
        except:
            slug = None

        try:
            title = event.find('div', {'class': 'preview-event__left'}).find('a').get_text().strip()
        except:
            title = None

        try:
            tags = event.find('span', {'class': 'event-label'}).find_all('span')
            tags = [tag.get_text().strip() for tag in tags]
        except:
            tags = None

        try:
            urls = event.find('div', {'class': 'event-buttons'}).find_all('a')
            urls = [url['href'] for url in urls]
        except:
            urls = None

        urls_dict = {'other': []}
        # try to match urls to their type
        if urls is not None:
            for url in urls:
                if re.search('ticket', url):
                    urls_dict['ticket'] = url
                elif re.search('program', url) and url.startswith('/'):
                    urls_dict['info'] = base_url + url
                elif re.search('program', url) and url.startswith('http'):
                    urls_dict['info'] = url
                elif re.search('\.ics', url):
                    urls_dict['cal'] = url
                else:
                    urls_dict['other'].append(url)

        if urls_dict.get('info') is None:
            urls_dict['info'] = base_url + slug



        try:
            description = event.find('div', {'class': 'preview-event__text'})
        except:
            description = None

        desc_p = description.find_all('p')


        # try to match the time and the rest will be location
        time = None
        location = None

        if len(desc_p) > 0:

            time_match = re.findall(r'(–*\s*[0-9]{1,2}:[0-9]{1,2}\s*)', desc_p[0].get_text().strip())

            if time_match is not None:
                time = ''.join(time_match)
                location = desc_p[0].get_text().strip().replace(time, '').strip()

        description = None

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





        if len(desc_p) > 1:
            description = ''
            for i, p in enumerate(desc_p):
                if i > 0:
                    description = description + " " + p.get_text().strip()


        # add to schedule_events
        schedule_events.append({'date': utils.ymd_string(date),
                                'year': utils.get_year(date),
                                'kw': utils.get_weeknum(date),
                                'venue': venue,
                                'slug': slug,
                                'title': title,
                                'tags': tags,
                                'urls': urls_dict,
                                'time': time,
                                'cost': None, # TODO: add cost
                                'start_datetime': start_datetime.isoformat() if start_datetime is not None else None,
                                'end_datetime': end_datetime.isoformat() if end_datetime is not None else None,
                                'location': location,
                                'description': description})

# write out to json
utils.write_json(schedule_events, 'kammerspiele_schedule.json')




