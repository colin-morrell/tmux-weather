# tmux-weather

tmux plugin that shows the current weather in the status bar, e.g. `Denver [emoji]  77°F`.

tmux runs the script on every status refresh (`status-interval`). Most runs just print a
cached result; the weather is only fetched again once the cache is older than
`@tmux-weather-refresh-interval`.

Requires `python3` (3.10+) on `PATH`. No third-party packages: everything is stdlib.

## Install

With [TPM](https://github.com/tmux-plugins/tpm), add to `~/.tmux.conf`:

```
set -g @plugin 'colin-morrell/tmux-weather'
```

then put `#{tmux-weather}` in `status-right` (or `status-left`):

```
set -g status-right '#{tmux-weather} | %H:%M'
```

and press `prefix` + `I` to install.

`status-right`/`status-left` must be set before TPM's `run '~/.tmux/plugins/tpm/tpm'` line,
since that's when `#{tmux-weather}` gets replaced.

## Options

| option | default | description |
|---|---|---|
| `@tmux-weather-refresh-interval` | `30` | minutes before the cached weather is fetched again |
| `@tmux-weather-cache` | `~/.cache/tmux-weather/latest` | cached `<timestamp> <weather>` line |
| `@tmux-weather-logfile` | (none) | log file; every line starts with a `YYYY-MM-dd: HH-mm-ss` timestamp. No logging if unset |
| `@tmux-weather-strip-variation-selector` | `off` | `on` strips U+FE0F from the weather icon (see [Known issues](#known-issues)) |

e.g.

```
set -g @tmux-weather-refresh-interval 30  # minutes
set -g @tmux-weather-cache '/mnt/e/log/tmux-weather-latest.log'
set -g @tmux-weather-logfile '/mnt/e/log/tmux-weather.log'
set -g @tmux-weather-strip-variation-selector on
```

## How it works

`tmux-weather.tmux` runs once when TPM loads the plugin. It reads the options above and
replaces `#{tmux-weather}` in `status-left`/`status-right` with:

```
#(python3 '<plugin dir>/scripts/weather.py' --refresh-interval '30' --cache '...' --logfile '...')
```

`scripts/weather.py` then runs on every status refresh:

1. Read the cache file, a single line holding a timestamp and the weather:
   ```
   2026-10-04: 13-57-25 Denver [emoji]  77°F
   ```
2. If that file is missing or empty, its timestamp can't be parsed, or the timestamp is at
   least `refresh-interval` minutes old, fetch the weather (`scripts/fetch.py`):
   - location (city + coordinates) from https://ipinfo.io, based on the machine's IP
   - weather for those coordinates from https://wttr.in (`?format=3`)
   - overwrite the cache with the current timestamp + weather

   If any step fails, the error is logged and the old cache is left as is.
3. Print the weather from the cache (without the timestamp) for tmux to display.

Runs that don't fetch log nothing, so the log isn't flooded by tmux's status refreshes.
`fetch.py` is only imported when a fetch is needed.

## Overhead

Average time per run (WSL, system `python3` 3.12):

| run | average |
|---|---|
| no fetch | 34 ms (20 runs) |
| fetch | 538 ms (5 runs; depends on network and the two APIs) |

With `status-interval 5` and a 30 minute refresh interval, that's ~34 ms every 5 seconds plus
one fetch every ~30 minutes.

## Development

Poetry is only used for dev tools (ipython, rich); the plugin itself has no dependencies.

To run a local copy as the plugin, symlink it into TPM's plugin dir (TPM skips cloning
plugins that already exist) and reload tmux:

```sh
ln -s ~/custom/tmux-weather ~/.tmux/plugins/tmux-weather
tmux source-file ~/.tmux.conf
```

## Known issues

- tmux < 3.5 counts emoji with a variation selector (U+FE0F, e.g. sunny/cloudy) as 1 cell
  wide, while some terminals (e.g. Windows Terminal) draw them 2 wide, leaving an unstyled
  cell after the emoji. Set `@tmux-weather-strip-variation-selector on` to strip U+FE0F, or
  upgrade to tmux >= 3.5 (`variation-selector-always-wide`, on by default).
- The location comes from the machine's public IP, so a VPN will report the VPN's location.
