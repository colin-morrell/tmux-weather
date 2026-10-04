import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

TIMESTAMP_FMT = '%Y-%m-%d %H:%M:%S'

log = logging.getLogger('tmux-weather')


def parse_args() -> argparse.Namespace:
    # options come from tmux-weather.tmux, which reads them from the @tmux-weather-* tmux options
    parser = argparse.ArgumentParser(description='print the current weather for tmux status bar')
    parser.add_argument('--refresh-interval', type=int, default=30,
                        help='minutes before the cached weather is fetched again')
    parser.add_argument('--cache', default=str(Path.home() / '.cache' / 'tmux-weather' / 'latest'),
                        help='file holding the latest weather')
    parser.add_argument('--logfile', default='',
                        help='log file (no logging if empty)')
    parser.add_argument('--strip-variation-selector', action='store_true',
                        help='strip U+FE0F from the weather icon (for tmux < 3.5)')
    return parser.parse_args()


def setup_logging(logfile: str) -> None:
    if not logfile:
        # otherwise python's last-resort handler prints warnings/errors to stderr
        log.addHandler(logging.NullHandler())
        log.propagate = False
        return

    Path(logfile).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt=TIMESTAMP_FMT,
    )


def read_latest(cache: str) -> str:
    try:
        return Path(cache).read_text().strip()
    except FileNotFoundError:
        return ''


def is_stale(cache: str, refresh_interval: int) -> bool:
    """Whether or not a fetch is needed."""
    line = read_latest(cache)
    # cache empty/missing --> fetch
    if not line:
        return True

    # line is '<date> <time> <weather>', e.g. '2026-10-04 11:43:21 Denver [emoji]  70[degree]F'
    try:
        date, time, _ = line.split(' ', 2)
        timestamp = datetime.strptime('{} {}'.format(date, time), TIMESTAMP_FMT)
    except ValueError:
        # timestamp mangled --> fetch
        log.warning('[!] bad timestamp in {}: {}'.format(cache, line))
        return True

    # time elapsed since cached fetch
    delta = datetime.now() - timestamp

    # bool: whether or not we're past refresh interval
    return delta >= timedelta(minutes=refresh_interval)


def write_weather(cache: str, weather: str) -> None:
    latest = Path(cache)
    latest.parent.mkdir(parents=True, exist_ok=True)
    line = '{} {}'.format(datetime.now().strftime(TIMESTAMP_FMT), weather)
    latest.write_text(line + '\n')
    log.info('[+] wrote "{}" to {}'.format(line, latest))


def fetch_weather(args: argparse.Namespace) -> None:
    # only import fetch (and urllib/json) when we need it
    from fetch import location, weather

    log.info('[.] latest weather is empty or stale, fetching')

    loc = location()
    if loc is None:
        log.error('[!] loc obj received from location() is None')
        return

    weather = weather(loc, args.strip_variation_selector)
    if weather is None:
        log.error('[!] weather obj received from weather() is None')
        return

    write_weather(args.cache, weather)


def main():

    args = parse_args()
    setup_logging(args.logfile)

    if is_stale(args.cache, args.refresh_interval):
        fetch_weather(args)

    parts = read_latest(args.cache).split(' ', 2)
    print(parts[2] if len(parts) == 3 else 'error fetching weather :(')


if __name__ == '__main__':
    main()
