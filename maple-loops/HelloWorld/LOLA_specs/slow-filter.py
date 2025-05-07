import paho.mqtt.client as mqtt
import time
from dataclasses import dataclass
import dataclasses
import datetime
import json
import sys

argc = len(sys.argv)
if argc != 4:
    print(f'Usage: {sys.argv[0]} [source_topic] [output_topic] [max_rate]')
    sys.exit(1)

SYNC_SOURCE_TOPIC=sys.argv[1]
SYNC_OUTPUT_TOPIC=sys.argv[2]
SYNC_RATE=float(sys.argv[3])

print(f'{SYNC_SOURCE_TOPIC=} {SYNC_OUTPUT_TOPIC=} {SYNC_RATE=}')

time_func = time.time

last_tx = 0
ignored = 0



def encode_value(x):
    if dataclasses.is_dataclass(x):
        return x.__dict__
    elif isinstance(x, datetime.datetime):
        return x.isoformat()
    # other special cases... 

    return x

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    # Be careful, the reason_code_list is only present in MQTTv5.
    # In MQTTv3 it will always be empty
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
    else:
        print(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()

def on_message(client, userdata, message):
    global last_tx
    global ignored

    topic = str(message.topic)
    
    if topic == SYNC_SOURCE_TOPIC:
        now = time_func()

        if now - last_tx >= SYNC_RATE:
            msg = message.payload
            client.publish(SYNC_OUTPUT_TOPIC, msg)
            last_tx = now
            print("\n" + str(msg))
            ignored = 0
        else:
            print(f'\rSkipped ({ignored+1})', end='')
            ignored += 1


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        client.subscribe(SYNC_SOURCE_TOPIC)


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

mqttc.connect("localhost")

try:
    mqttc.loop_forever()
    pass
except KeyboardInterrupt:
    stop = True
    print()
finally:
    mqttc.loop_stop()
