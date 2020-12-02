"""
Bridges USB connection to valve board and MQTT eventbus
"""

import json
import signal
import traceback
from os import getenv
from queue import Queue

import serial
from paho.mqtt import client as mqtt
from serial.threaded import LineReader, ReaderThread

MQTT_HOST = getenv('MQTT_HOST', 'eventbus')
SERIAL_PORT = getenv('SERIAL_PORT', '/dev/ttyACM0')
SERIAL_BAUDRATE = getenv('SERIAL_BAUDRATE', 9600)
FIELDS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
CONFIG = {
    'id': 'valve-hack',
    'title': 'Valve Hack',
    'fields': FIELDS,
    'editable': True,
    'valueName': {v: f'Valve {v}' for v in FIELDS},
    'valueType': 'enum',
    'choices': ['open', 'closed'],
}


ser = serial.Serial()
client = mqtt.Client()
msg_q = Queue()


def sig_handler(signum, frame):
    raise KeyboardInterrupt()


def strex(ex):
    return f'{type(ex).__name__}({str(ex)})'


def on_connect(client, userdata, flags, rc):
    print('MQTT connected')
    client.subscribe('brewcast/device/change/valve-hack')
    client.publish('brewcast/device/config/valve-hack',
                   json.dumps(CONFIG),
                   retain=True)


def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload)
        cmd = ''.join([
            k + ('1' if v == 'open' else '0')
            for k, v in data['desiredValues'].items()])
        msg_q.put(('serial', cmd))

    except Exception as ex:
        traceback.print_exc(ex)


def on_disconnect(client, userdata, rc):
    print('MQTT disconnected')


class SerialHandler(LineReader):

    TERMINATOR = b'\n'

    def connection_made(self, transport):
        super().connection_made(transport)
        print('Serial connected')
        msg_q.put(('serial', '?'))  # Prompt status response

    def handle_line(self, data):
        try:
            data = data.rstrip()

            if '|' in data:
                print(data)
                return

            if data:
                keys = data[::2]
                values = ['open' if v == '1' else 'closed' for v in data[1::2]]
                msg = {
                    'id': 'valve-hack',
                    'values': {k: v for (k, v) in zip(keys, values)}
                }
                msg_q.put(('mqtt', msg))

        except Exception as ex:
            traceback.print_exc(ex)

    def connection_lost(self, exc):
        super().connection_lost(exc)
        print('Serial disconnected')


try:
    signal.signal(signal.SIGTERM, sig_handler)

    print(f'================ serial={SERIAL_PORT}, mqtt={MQTT_HOST} ================')

    ser.port = SERIAL_PORT
    ser.baudrate = SERIAL_BAUDRATE
    ser.open()

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect_async(host=MQTT_HOST)
    client.loop_start()

    with ReaderThread(ser, SerialHandler) as protocol:
        protocol: LineReader
        while True:
            target, msg = msg_q.get()
            print('Sending', target, msg)

            if target == 'serial':
                protocol.write_line(msg)

            if target == 'mqtt':
                client.publish('brewcast/device/state/valve-hack',
                               json.dumps(msg),
                               retain=True)

except KeyboardInterrupt:
    pass

except Exception as ex:
    traceback.print_exc(ex)

finally:
    client.loop_stop()
    ser.close()
