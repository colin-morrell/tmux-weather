import json
import logging
import urllib.request

log = logging.getLogger('tmux-weather')

TIMEOUT = 10  # seconds


def http_get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as res:
        return res.read().decode()


def get_location() -> dict | None:
    """Get machine's location via IP."""

    # TODO --> VPN will almost certainly break this

    url = 'https://ipinfo.io'
    try:
        loc = json.loads(http_get(url))
    # OSError covers urllib.error.URLError/HTTPError and timeouts
    except (OSError, ValueError) as e:
        log.error('[!] failed to get location from {}: {}'.format(url, e))
        return None
    log.info('[+] location: {} ({})'.format(loc.get('city'), loc.get('loc')))
    return loc


def get_weather(loc: dict, strip_variation_selector: bool = False) -> str | None:
    coordinates = loc['loc']
    url = 'https://wttr.in/{}?format=3'.format(coordinates)
    try:
        text = http_get(url)
        parts = text.split()

        # parts[0] is coordinates, so grab city from ipinfo call
        city = loc['city']
        icon = parts[1]
        temp = parts[2].strip('+')
    except (OSError, UnicodeDecodeError) as e:
        log.error('[!] failed to get weather from {}: {}'.format(url, e))
        return None
    except (IndexError, KeyError) as e:
        log.error('[!] unexpected weather response {}: {}'.format(text, e))
        return None

    # strip emoji variation selector (U+FE0F): tmux < 3.5 counts some emoji
    # as 1 cell wide but winterminal draws it as 2, leaving an unstyled
    # (i.e. black) cell after it
    if strip_variation_selector:
        icon = icon.replace('️', '')

    return '{} {}  {}'.format(city, icon, temp)
