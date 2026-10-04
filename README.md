# tmux-weather

tmux plugin that shows the current weather in the status bar with minimal overhead, e.g. `Denver ☀️  77°F`.

- script runs on every status refresh (`status-interval`)
- weather is fetched only if cache is empty or cache is older than `@tmux-weather-refresh-interval`
- non-fetch runs average ~35ms overhead
- fetch runs average ~540ms

## requirements

- python3.10+
- tmux v??

## install

with [TPM](https://github.com/tmux-plugins/tpm), add to `~/.tmux.conf`:

```
set -g @plugin 'colin-morrell/tmux-weather'
```

then put `#{tmux-weather}` in `status-right`/`status-left`:

```
set -g status-right '#{tmux-weather} | %H:%M'
```

then press `prefix` + `I` to install.

## options

| option | default | description |
|---|---|---|
| `@tmux-weather-refresh-interval` | `30` | minutes between fetches |
| `@tmux-weather-cache` | `~/.cache/tmux-weather/latest` | cached `<timestamp> <weather>` line |
| `@tmux-weather-logfile` | (none) | log file. no logging if unset |
| `@tmux-weather-strip-variation-selector` | `off` | `on` strips U+FE0F from the weather icon (see [known issues](#known-issues)) |

e.g.

```
set -g @tmux-weather-refresh-interval 30  # minutes
set -g @tmux-weather-cache '/mnt/e/log/tmux-weather-latest.log'
set -g @tmux-weather-logfile '/mnt/e/log/tmux-weather.log'
set -g @tmux-weather-strip-variation-selector on
```

## overhead

overhead is kept (relatively) light by using only standard libraries and conditional imports.

average runtime (win10/WSL, system `python3` 3.12):

- no-fetch: 34ms (n=20)
- fetch: 538ms (n=5)

fetch runs are network-bound and likely to be variable.

no-fetch runs are kept light by skipping the `fetch.py` importd.

## development

plugin has no dependencies. 

poetry is used for dev tools (ipython, rich).

to run a local copy, symlink it into TPM's plugin dir (TPM skips cloning plugins that already exist) and reload tmux:

```sh
ln -s [local path]/tmux-weather ~/.tmux/plugins/tmux-weather
tmux source-file ~/.tmux.conf
```

## known issues

- tmux < 3.5 counts emoji with a variation selector (U+FE0F, e.g. sunny/cloudy) as 1 cell
  wide, while some terminals (looking at you winterminal) draw them 2 wide, leaving an unstyled (i.e. black)
  cell after the emoji. Set `@tmux-weather-strip-variation-selector on` to strip U+FE0F, or
  upgrade to tmux >= 3.5 (`variation-selector-always-wide`, on by default).
- location is derived from host's public IP, so a VPN will report the VPN's location.
