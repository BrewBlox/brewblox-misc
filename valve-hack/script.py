"""
Bridges USB connection to valve board and MQTT eventbus
"""

import json
from os import getenv

import serial
from paho.mqtt import client as mqtt

FIELDS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
CONFIG = {
    'id': 'valve-hack',
    'title': 'Valve Hack',
    'fields': FIELDS,
    'editable': True,
    'valueName': {v: f'Valve {v.upper()}' for v in FIELDS},
    'valueType': 'enum',
    'choices': ['open', 'closed'],
}


ser = serial.Serial(port=getenv('PORT', '/dev/ttyACM0'),
                    baudrate=9600,
                    timeout=1)
client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print('connected!')
    client.subscribe('brewcast/device/change/valve-hack')
    client.publish('brewcast/device/config/valve-hack',
                   json.dumps(CONFIG),
                   retain=True)


def on_message(client, userdata, message):
    data = json.loads(message.payload)
    raw = ''.join([
        k + ('1' if v == 'open' else '0')
        for k, v in data['setting'].items()])
    print('writing', raw)
    if ser.is_open:
        ser.write(raw.encode() + b'\n')


try:
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect_async(host='eventbus')
    client.loop_start()

    buffer = ''

    while True:
        buffer += ser.read(8 + 8 + 1).decode()
        output = buffer.splitlines(True)

        if not output:
            continue

        if output[-1].endswith('\n'):
            buffer = ''
        else:
            buffer = output.pop()  # send incomplete message back to buffer

        if output:
            data = output.pop().rstrip()  # We only care about the last message
            keys = data[::2]
            values = ['open' if v == '1' else 'closed' for v in data[1::2]]
            print('publishing', values)
            client.publish('brewcast/device/state/valve-hack',
                           json.dumps({
                               'id': 'valve-hack',
                               'value': {k: v for (k, v) in zip(keys, values)}
                           }),
                           retain=True)

finally:
    print('Stopping...')
    client.loop_stop()
    ser.close()
