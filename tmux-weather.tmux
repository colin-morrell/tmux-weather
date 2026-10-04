#!/usr/bin/env bash

# TPM runs this on load: replace #{tmux-weather} in status-left/status-right
# with a #() call to scripts/weather.py, built from the @tmux-weather-* options

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

get_tmux_option() {
    local value
    value="$(tmux show-option -gqv "$1")"
    echo "${value:-$2}"
}

main() {
    local refresh_interval cache logfile strip cmd placeholder option value
    refresh_interval="$(get_tmux_option @tmux-weather-refresh-interval 30)"
    cache="$(get_tmux_option @tmux-weather-cache "$HOME/.cache/tmux-weather/latest")"
    logfile="$(get_tmux_option @tmux-weather-logfile '')"
    strip="$(get_tmux_option @tmux-weather-strip-variation-selector off)"

    cmd="python3 '$CURRENT_DIR/scripts/weather.py' --refresh-interval '$refresh_interval' --cache '$cache' --logfile '$logfile'"
    if [ "$strip" = on ]; then
        cmd="$cmd --strip-variation-selector"
    fi

    # quoting the pattern makes bash match #{ literally; quoting the replacement keeps & literal
    placeholder='#{tmux-weather}'
    for option in status-left status-right; do
        value="$(tmux show-option -gqv "$option")"
        tmux set-option -gq "$option" "${value//"$placeholder"/"#($cmd)"}"
    done
}
main
