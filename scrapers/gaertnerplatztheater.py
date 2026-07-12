import utils
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

tz = 'Europe/Berlin'
venue = 'Gärtnerplatztheater'
short_id = 'gtp'

current_year = utils.get_current_year()

base_url = 'https://www.gaertnerplatztheater.de/'
spielplan_url = 'https://www.gaertnerplatztheater.de/de/spielplan/index.html'

schedule_events = []


def get_all_performances():
    """
    Load all performances via the site's ajax pagination endpoint.

    The schedule is rendered client-side: the page repeatedly POSTs to
    ?ajax=1&offset={page}&letzterTermin={ts}, incrementing the page and
    carrying the last termin timestamp from each response, until the server
    replies "ende erreicht.". This avoids driving the animation-heavy page
    through Selenium, whose renderer hangs on it.
    """
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; ghxm.github.io/theatermuc/ data collection'})

    # retry transient connection/read timeouts and 5xx responses
    retry = Retry(total=4, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=frozenset(['GET', 'POST']))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    # seed the session cookie by loading the page once
    session.get(spielplan_url, timeout=(30, 60))

    ajax_headers = {'X-Requested-With': 'XMLHttpRequest', 'Referer': spielplan_url}

    performances = []
    page = 0
    letzter = '0'
    empty_streak = 0

    # page 1 is legitimately empty; only "ende erreicht." ends the sequence
    while page < 120:
        r = session.post(f'{spielplan_url}?ajax=1&offset={page}&letzterTermin={letzter}',
                         headers=ajax_headers, timeout=(30, 60))
        r.raise_for_status()

        if r.text.strip() == 'ende erreicht.':
            break

        page_perfs = utils.make_soup(r.text).find_all('div', class_='performance')
        performances.extend(page_perfs)

        match = re.search(r'<div class="d-none letzterTermin">(.+?)</div>', r.text)
        if match:
            letzter = match.group(1)

        empty_streak = 0 if page_perfs else empty_streak + 1
        if empty_streak > 15:
            break
        page += 1

    return performances


print(f'Loading {spielplan_url}')
performances = get_all_performances()
print(f'Found {len(performances)} performances')

for performance in performances:
    try:
        # Extract date - look for pattern like "So, 01.02.26"
        date_elem = performance.find('div', class_='fs-3')
        if date_elem:
            date_text = date_elem.get_text().strip()
            # Remove weekday prefix like "So, "
            date_clean = re.sub(r'^[A-Za-z]{2,3},\s*', '', date_text)
            # Convert DD.MM.YY to DD.MM.YYYY
            if len(date_clean.split('.')) == 3 and len(date_clean.split('.')[-1]) == 2:
                day, month, year = date_clean.split('.')
                year = '20' + year if int(year) < 50 else '19' + year
                date_clean = f"{day}.{month}.{year}"
        else:
            date_clean = None

        # Extract time
        time_elem = performance.find('div', class_='fw-bold')
        if time_elem:
            time_text = time_elem.get_text().strip()
            # Extract time pattern like "15.00–17.55 Uhr"
            time_match = re.search(r'(\d{1,2}\.\d{2})(?:–(\d{1,2}\.\d{2}))?\s*Uhr', time_text)
            if time_match:
                start_time = time_match.group(1).replace('.', ':')
                end_time = time_match.group(2).replace('.', ':') if time_match.group(2) else None
            else:
                start_time = None
                end_time = None
        else:
            start_time = None
            end_time = None

        # Extract title
        title_elem = performance.find('a')
        if title_elem:
            title = title_elem.get_text().strip()
        else:
            title = None

        # Extract genre/sparte
        genre_elem = performance.find('span', class_='text-uppercase')
        if genre_elem:
            genre = genre_elem.get_text().strip()
        else:
            genre = None

        # Extract URLs
        urls_dict = {}
        slug = None
        if title_elem and title_elem.get('href'):
            slug = title_elem['href']
            if slug.startswith('./'):
                slug = slug[2:]
            urls_dict['info'] = base_url + 'de/' + slug

        # Extract location from CSS classes
        location = None
        classes = performance.get('class', [])
        for cls in classes:
            if cls.startswith('ort-'):
                # Map ort IDs to locations
                if cls == 'ort-57':
                    location = 'Bühne'
                elif cls == 'ort-58':
                    location = 'Foyer'
                elif cls == 'ort-92':
                    location = 'Orchesterprobensaal'
                elif cls == 'ort-107':
                    location = 'Studiobühne'
                break

        # Create datetime objects
        try:
            start_datetime = utils.make_datetime(date_clean, start_time, tz) if date_clean and start_time else None
        except:
            start_datetime = None

        try:
            end_datetime = utils.make_datetime(date_clean, end_time, tz) if date_clean and end_time else None
        except:
            end_datetime = None

        if date_clean is None or title is None:
            print(f'Skipping event with missing date ({date_clean}) or title ({title})')
            continue

        # Add to schedule_events
        schedule_events.append({
            'date': utils.ymd_string(date_clean),
            'year': utils.get_year(date_clean),
            'kw': utils.get_weeknum(date_clean),
            'venue': venue,
            'slug': slug,
            'title': title,
            'tags': [genre] if genre else [],
            'urls': urls_dict,
            'time': f"{start_time} Uhr" if start_time else None,
            'cost': None,
            'start_datetime': start_datetime.isoformat() if start_datetime else None,
            'end_datetime': end_datetime.isoformat() if end_datetime else None,
            'location': location,
            'description': genre
        })

    except Exception as e:
        print(f'Error parsing performance: {e}')
        continue

print(f'Total events found: {len(schedule_events)}')

# Write to file
utils.write_json(schedule_events, 'gaertnerplatztheater_schedule.json')
