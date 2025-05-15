import paho.mqtt.client as mqtt
import time
from dataclasses import dataclass
import dataclasses
import datetime
import json

from dyn_lola.shapes import turtlebot

PREFIX='lola/walls2-redux.lola/'

@dataclass
class XYCoord:
    x: float
    y: float

    def as_list(self):
        return [self.x, self.y]

@dataclass
class RobotPosition:
    Center: XYCoord
    Corners: dict[str, XYCoord]
    Collisions: dict[str, bool]
    Obstacle: list[XYCoord]

    def grafana_dict(self):
        colors = {
            'center': 0,
            'corner_no_collision': 1,
            'corner_collision': 2,
            'obstacle': 3
        }

        corners = []
        for corner, collision in zip(self.Corners.values(), self.Collisions.values()):
            corners.append(corner.as_list())
            if collision:
                corners[-1] += [colors['corner_collision']]
            else:
                corners[-1] += [colors['corner_no_collision']]

        return {
            'center': [self.Center.as_list() + [colors['center']]],
            'corners': corners,
            'obstacles': [obst.as_list() + [colors['obstacle']] for obst in self.Obstacle]
        }

def encode_value(x):
    if dataclasses.is_dataclass(x):
        return x.__dict__
    elif isinstance(x, datetime.datetime):
        return x.isoformat()
    # other special cases... 

    return x

from math import sqrt
from itertools import chain, combinations_with_replacement
r = 0.15
r2 = r/sqrt(2)
pillars = list(chain.from_iterable([[
    XYCoord(i*1.1+r, j*1.1),
    XYCoord(i*1.1-r, j*1.1),
    XYCoord(i*1.1, j*1.1+r),
    XYCoord(i*1.1, j*1.1-r),
    XYCoord(i*1.1+r2, j*1.1+r2),
    XYCoord(i*1.1+r2, j*1.1-r2),
    XYCoord(i*1.1-r2, j*1.1-r2),
    XYCoord(i*1.1-r2, j*1.1+r2)
]
for i in range(-1,2) for j in range(-1,2)
]))

latest_telemetry = RobotPosition(XYCoord(0,0), Corners=dict(), Collisions=dict(), Obstacle=[
    XYCoord(-0.1, 2.1),
    XYCoord(-0.1, 1.9),
    XYCoord( 0.1, 1.9),
    XYCoord( 0.1, 2.1)]
    + [XYCoord(x,y) for x,y in turtlebot.turtle_map]
    + pillars)
last_tx = 0
update_period = 0.50 #s

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

    topic = topic.removeprefix(PREFIX)

    match topic:
        case "x":
            latest_telemetry.Center.x = msg.get('Float')
        case "y":
            latest_telemetry.Center.y = msg.get('Float')
        
    for x in range(4):
        if topic == f"C{x}X":
            latest_telemetry.Corners[x].x = msg.get('Float')
        elif topic == f"C{x}Y":
            latest_telemetry.Corners[x].y = msg.get('Float')
        elif topic == f"Corner{x}Collision":
            latest_telemetry.Collisions[x] = msg.get('Bool')

    if last_tx + update_period < current_time:
        client.publish('telemetry/collision', json.dumps(latest_telemetry, default=encode_value))
        for k,v in latest_telemetry.grafana_dict().items():
            client.publish(f'telemetry/collision2/{k}', json.dumps(v, default=encode_value))
        last_tx = current_time


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        client.subscribe(PREFIX+"x")
        client.subscribe(PREFIX+"y")
        for x in range(4):
            latest_telemetry.Corners[x] = XYCoord(0,0)
            latest_telemetry.Collisions[x] = False
            client.subscribe(PREFIX+f'C{x}X')
            client.subscribe(PREFIX+f'C{x}Y')
            client.subscribe(PREFIX+f'Corner{x}Collision')


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
