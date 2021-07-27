#!/bin/bash
set -euo pipefail
trap 'pkill -P $$; exit 1;' TERM INT

# Default Docker host IP. Replace this if you're running on the host.
HOST="172.17.0.1"

# MQTT Topic for publishing Brewblox history.
TOPIC="brewcast/history/pi-temperature"

# We want to use a variable in a string that contains double quotes.
# We build a template as single quoted string, and later replace '#TEMP' with the variable.
# This avoids having to escape all double quotes in the string itself.
TEMPLATE='{"key": "pi-temperature", "data": {"temperature[degC]": #TEMP}}'

while :
do
    # Make sleep a background process, and wait for it.
    # This handles SIGINT immediately when received.
    sleep 10 &
    wait $!

    # Get temperature in millidegC.
    TEMP_MILLI_C=$(cat /sys/class/thermal/thermal_zone0/temp)

    # Convert temp to degC.
    TEMP_C="$(perl -e "print ${TEMP_MILLI_C} / 1000")"

    # Replace '#TEMP' string in the template with numeric value.
    # Publish the JSON string as MQTT message.
    # Ignore publish errors: maybe the eventbus is still starting.
    mosquitto_pub -h "$HOST" -t "$TOPIC" -m "${TEMPLATE//#TEMP/${TEMP_C}}" || true
done
