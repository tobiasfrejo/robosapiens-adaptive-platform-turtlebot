import paho.mqtt.client as mqtt
import time
from dataclasses import dataclass
import dataclasses
import datetime
import json
from math import cos, sin

PREFIX='lola/ghost.lola/'

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

    def test_dict(self):
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
from itertools import chain
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

turtle_map = [
    XYCoord(-2.8868,  0.0),
    XYCoord(-1.7248, -2.0125),
    XYCoord(-1.4031, -2.0125),
    XYCoord(-1.1216, -2.5),
    XYCoord( 1.1216, -2.5),
    XYCoord( 1.4031, -2.0125),
    XYCoord( 1.7248, -2.0125),
    XYCoord( 2.616,  -0.4689),
    XYCoord( 2.3453,  0.0),
    XYCoord( 2.616,   0.4689),
    XYCoord( 1.7248,  2.0125),
    XYCoord( 1.4031,  2.0125),
    XYCoord( 1.1216,  2.5),
    XYCoord(-1.1216,  2.5),
    XYCoord(-1.4031,  2.0125),
    XYCoord(-1.7248,  2.0125),
]
sock = [
    XYCoord(-0.1, 2.1),
    XYCoord(-0.1, 1.9),
    XYCoord( 0.1, 1.9),
    XYCoord( 0.1, 2.1),
]

from dyn_lola.shapes.turtlebot import tb3_corners



latest_telemetry = RobotPosition(XYCoord(0,0), Corners=dict(), Collisions=dict(), Obstacle=turtle_map+pillars)
last_tx = 0
update_period = 0.50 #s
latest_ghost = {
    'x': 0,
    'y': 0,
    'a': 0
}

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

    send_update = False
    if last_tx + update_period < current_time:
        send_update = True

    match topic:
        case "x":
            latest_telemetry.Center.x = msg.get('Float')
            print('new x', latest_telemetry.Center.x)
        case "y":
            latest_telemetry.Center.y = msg.get('Float')
            print('new y', latest_telemetry.Center.y)
        case "telemetry/ghost/pos":
            print("New ghost pos:", msg)
            ghost_corners = [
                XYCoord(
                    x*cos(msg.get('a')) - y * sin(msg.get('a')) + msg.get('x'),
                    x*sin(msg.get('a')) + y * cos(msg.get('a')) + msg.get('y'),
                )
                for (x,y) in tb3_corners
            ]
            latest_telemetry.Obstacle = turtle_map + pillars + ghost_corners
            send_update = True 
        
    for x in range(4):
        if topic == f"C{x}X":
            latest_telemetry.Corners[x].x = msg.get('Float')
        elif topic == f"C{x}Y":
            latest_telemetry.Corners[x].y = msg.get('Float')
        elif topic == f"Corner{x}Collision":
            latest_telemetry.Collisions[x] = msg.get('Bool')

    if send_update:
        for i in range(2):
            print(f'Publishing after {msg=}')
            try:
                print(ghost_corners)
                print(latest_telemetry)
            except:
                pass
            client.publish('telemetry/debug', str(msg))
            client.publish('telemetry/collision', json.dumps(latest_telemetry, default=encode_value))
            for k,v in latest_telemetry.test_dict().items():
                client.publish(f'telemetry/collision2/{k}', json.dumps(v, default=encode_value))
            last_tx = current_time
            time.sleep(0.01)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        client.subscribe('telemetry/ghost/pos')
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
    # while True:
    #     print('Main loop publish')
    #     for k,v in latest_telemetry.test_dict().items():
    #         mqttc.publish(f'telemetry/collision2/{k}', json.dumps(v, default=encode_value))
    #     time.sleep(update_period)
    # pass
except KeyboardInterrupt:
    stop = True
finally:
    mqttc.loop_stop()
