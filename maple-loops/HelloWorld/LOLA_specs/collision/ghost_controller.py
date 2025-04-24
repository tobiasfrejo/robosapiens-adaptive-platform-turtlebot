from itertools import chain
import json
from time import sleep
import sys

import paho.mqtt.client as mqtt

from dyn_lola.geometry import connect_polygon, rotate_polygon
from dyn_lola.lola import LolaSpecification, LolaStream, lola_chain
from dyn_lola.pnpoly import pnpoly
from dyn_lola.shapes import turtlebot


def get_ghost_spec(pos):
    spec = LolaSpecification()

    # TurtleBot position
    x = LolaStream('x')
    y = LolaStream('y')
    a = LolaStream('a')
    spec.inputs.append(x)
    spec.inputs.append(y)
    spec.inputs.append(a)

    ghost_exprs, ghost_rotated_corners = rotate_polygon(turtlebot.tb3_corners, (pos['x'],pos['y']), pos['a'], 'ghost')
    tb3_exprs, tb3_rotated_corners = rotate_polygon(turtlebot.tb3_corners, (x,y), a, 'tb3')

    tb3_edges = connect_polygon(tb3_rotated_corners)
    wall_exprs, pnp = pnpoly(ghost_rotated_corners, tb3_edges)

    for k,v in chain.from_iterable((ghost_exprs.items(), tb3_exprs.items(), wall_exprs.items())):
        spec.add_expression(k,v)

    ghost_collision = LolaStream('GhostCollision')
    spec.add_expression(ghost_collision, lola_chain(pnp, '||'), keep_on_prune=True)
    # print(spec.expressions.keys())
    # print(spec.get_specification_string())

    spec.collapse_expression(ghost_collision)
    spec.prune()

    return str(spec.expressions.get(ghost_collision))

"""
in x
in y
in a
collision = f(x,y,a)

dynamicwalls = {Str: f(x,y,a)}


in Odometry
in dynamicwalls
out a
out x
out y
...

collision = corner0collision || ... || eval(dynamicwalls)

"""





ghost_sequence = [
    {
        'x': 1.0,
        'y': -0.5,
        'a':  3.14,
    },
    {
        'x': 0.0,
        'y': -0.5,
        'a':  3.14,
    },
    {
        'x': -1.0,
        'y': -0.5,
        'a':  3.14,
    },
    {
        'x': -1.75,
        'y': -0.5,
        'a':  3.14,
    },
    {
        'x': -1.75,
        'y': -0.5,
        'a':  2.355,
    },
    {
        'x': -1.9,
        'y': -0.4,
        'a':  3.14,
    },
]



def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}.")
        sys.exit()
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        pass


print(get_ghost_spec(ghost_sequence[0]))

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.connect("localhost")
mqttc.loop_start()

try:
    while True:
        for step in ghost_sequence:
            spec = get_ghost_spec(step)
            mqttc.publish('GhostCollide3_raw', spec)
            mqttc.publish('telemetry/ghost/pos', json.dumps(step))
            print('new step: ', step)
            sleep(10)
except KeyboardInterrupt:
    print('Stopping...')
finally:
    mqttc.loop_stop()