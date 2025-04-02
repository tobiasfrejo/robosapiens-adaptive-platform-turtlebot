import paho.mqtt.client as mqtt
import time
from dataclasses import dataclass
import dataclasses
import datetime
import json

@dataclass
class XYCoord:
    x: float
    y: float

@dataclass
class RobotPosition:
    Center: XYCoord
    Corners: dict[str, XYCoord]
    Collisions: dict[str, bool]

def encode_value(x):
    if dataclasses.is_dataclass(x):
        return x.__dict__
    elif isinstance(x, datetime.datetime):
        return x.isoformat()
    # other special cases... 

    return x


latest_telemetry = RobotPosition(XYCoord(0,0), Corners=dict(), Collisions=dict())
last_tx = 0
update_period = 0.100 #s

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
    global update_period
    global latest_telemetry

    topic = str(message.topic)
    msg = json.loads(message.payload)

    current_time = time.time()
    
    # print(f'Got {msg} on {topic} at {current_time} (last update: {last_tx})')

    match topic:
        case "x":
            latest_telemetry.Center.x = msg.get('Float')
        case "y":
            latest_telemetry.Center.y = msg.get('Float')
        
    for x in range(4):
        if topic == f"RC{x}X":
            latest_telemetry.Corners[x].x = msg.get('Float')
        elif topic == f"RC{x}Y":
            latest_telemetry.Corners[x].y = msg.get('Float')
        elif topic == f"insideRC{x}":
            latest_telemetry.Collisions[x] = not msg.get('Bool')

    if last_tx + update_period < current_time:
        client.publish('telemetry/collision', json.dumps(latest_telemetry, default=encode_value))
        last_tx = current_time


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        client.subscribe("x")
        client.subscribe("y")
        for x in range(4):
            latest_telemetry.Corners[x] = XYCoord(0,0)
            latest_telemetry.Collisions[x] = False
            client.subscribe(f'RC{x}X')
            client.subscribe(f'RC{x}Y')
            client.subscribe(f'insideRC{x}')


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
finally:
    mqttc.loop_stop()
