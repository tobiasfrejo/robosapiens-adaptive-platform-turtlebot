import dataclasses
from dataclasses import dataclass
from math import cos, sin, pi
import time
import json
import sys

import paho.mqtt.client as mqtt


@dataclass
class Position:
    x: float = 0
    y: float = 0
    z: float = 0

@dataclass
class Orientation:
    x: float
    y: float
    z: float
    w: float

@dataclass
class Pose:
    position: Position
    orientation: Orientation = Orientation(0,0,0,1)

def from_euler(ai, aj, ak):
    i = ai/2
    j = aj/2
    k = ak/2

    ci = cos(i)
    si = sin(i)
    cj = cos(j)
    sj = sin(j)
    ck = cos(k)
    sk = sin(k)

    w = ci * cj * ck + si * sj * sk;
    x = si * cj * ck - ci * sj * sk;
    y = ci * sj * ck + si * cj * sk;
    z = ci * cj * sk - si * sj * ck;

    return Orientation(x,y,z,w)

def yaw(angle):
    return from_euler(0, 0, angle)

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)


steps = [
    Pose(
        Position(-2, -.5),
        yaw(pi/3)
    ),
    Pose(
        Position(-1.6, 0),
        yaw(pi/3)
    ),
    Pose(
        Position(-1, 0.6),
        yaw(0)
    ),
    Pose(
        Position(0.5, 0.6),
        yaw(pi/4)
    ),
    Pose(
        Position(1.6, 1.6),
        yaw(pi/4)
    ),
]


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}.")
        sys.exit(1)
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        pass


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.connect("localhost")
mqttc.loop_start()

try:
    for pose in steps:
        msg = json.dumps(pose, cls=EnhancedJSONEncoder)
        print(f'New Pose: {msg}')
        mqttc.publish('/goal_pose', msg)
        inp = input('Press enter to go to next pose')
        if inp.lower() in ["end", "stop", "e", "s"]:
            print("Stopping...")
            break
except KeyboardInterrupt:
    print('Stopping...')
finally:
    mqttc.loop_stop()