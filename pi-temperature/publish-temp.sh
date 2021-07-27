#!/bin/bash
set -euo pipefail
trap 'pkill -P $$; exit 1;' TERM INT

HOST="172.17.0.1" # Default Docker host IP
TOPIC="brewcast/history/pi-temperature"
TEMPLATE='{ "key": "pi-temperature", "data": { "temperature[degC]": #TEMP } }'
PATH="$PATH:/opt/vc/bin" # vcgencmd lives in /opt/vc/bin or /usr/bin

# Get vcgencmd measure_temp value (example: temp=45.7'C)
# Extract the numeric value with regex
# Replace '#TEMP' string in the template with numeric value
# Then publish the resulting JSON string as MQTT message
while :
do
    # call/wait sleep to handle SIGINT immediately
    sleep 10 &
    wait $!
    if [[ $(vcgencmd measure_temp) =~ temp=([0-9.]+) ]]; then
        mosquitto_pub -h "$HOST" -t "$TOPIC" -m "${TEMPLATE//#TEMP/${BASH_REMATCH[1]}}" || true
    fi
done
