from warnings import warn
import numpy as np
from itertools import chain
# Scaled to keep precision as ints

corners = np.array([
    (-2.8868,  0.0),
    (-1.7248, -2.0125),
    (-1.4031, -2.0125),
    (-1.1216, -2.5),
    ( 1.1216, -2.5),
    ( 1.4031, -2.0125),
    ( 1.7248, -2.0125),
    ( 2.616,  -0.4689),
    ( 2.3453,  0.0),
    ( 2.616,   0.4689),
    ( 1.7248,  2.0125),
    ( 1.4031,  2.0125),
    ( 1.1216,  2.5),
    (-1.1216,  2.5),
    (-1.4031,  2.0125),
    (-1.7248,  2.0125),
])

# obstacle1 = np.array([
#     (-3,  1),
#     (-1,  0),
#     ( 0, -3),
#     ( 0,  1)
# ])

def connect_polygon(corners):
    walls = []
    for i in range(len(corners)):
        j = (i - 1) % len(corners)
        walls.append((corners[i], corners[j]))
        # warn(f'({i}, {j}): {corners[i]}, {corners[j]}')
    walls = np.array(walls)
    return walls

walls = np.concat((
    connect_polygon(corners),
    # connect_polygon(obstacle1)
))
# warn(str(len(walls)))

# (Cx, Cy, R)
pillars = np.array([
    (-1.1,  -1.1,  0.15),
    (-1.1,   0.0,  0.15),
    (-1.1,   1.1,  0.15),
    ( 0.0,  -1.1,  0.15),
    ( 0.0,   0.0,  0.15),
    ( 0.0,   1.1,  0.15),
    ( 1.1,  -1.1,  0.15),
    ( 1.1,   0.0,  0.15),
    ( 1.1,   1.1,  0.15),
])

# Collision if distance to center is smaller than the radius.
#  (x-a)² + (y-b)² <= r²
"""
Could potentially be optimized to avoid extra multiplication operations if outside the circumscribed square:
(\
    PosX <= {cxpr} && \
    {cxmr} <= PosX && \
    PosY <= {cypr} && \
    {cymr} <= PosY
) && ...
"""
circle_collision_expression = '''\
(\
   ((({PosX} - {cx}) * ({PosX} - {cx})) \
  + (({PosY} - {cy}) * ({PosY} - {cy}))) \
    <= ({r} * {r})\
)'''

robot_corners_offsets = np.array([
    (-0.153, 0.1),
    ( 0.153, 0.1),
    (-0.153, -0.181),
    ( 0.153, -0.181)
])

robot_corners_names = []
declarations = []
for n, (x, y) in enumerate(robot_corners_offsets):
    rc = 'RC'+str(n)
    robot_corners_names.append(rc)
    declarations.append(f'{rc}X = ({x}) * cos(a) - ({y}) * sin(a) + x')
    declarations.append(f'{rc}Y = ({x}) * sin(a) + ({y}) * cos(a) + y')

"""
https://wrfranklin.org/Research/Short_Notes/pnpoly.html

(Ay > Py  !=  By > Py)
&&  (Px  <  (Bx-Ax) * (Py-Ay) / (By-Ay) + Ax)
"""


expression = """\
if !(\
!({ay} <= {PosY}) == !({by} <= {PosY})\
) && !(\
(({a}) * (({PosY}) - ({ay})) + ({ax})) <= ({PosX})) \
then 1 \
else 0 \
"""

streams = []
expressions = []
wall_names = []
walls_i = 0
for A, B in walls:
    Ax, Ay = A
    Bx, By = B

    if Ay == By:
        continue
    wx = 'w'+str(walls_i)
    for corner in robot_corners_names:
        streams.append(wx+corner)
        expr = (expression.format_map({
            'a':(Bx-Ax)/(By-Ay),
            'ax': Ax,
            'ay': Ay,
            'bx': Bx,
            'by': By,
            'PosX': corner+'X',
            'PosY': corner+'Y'
        }))
        declarations.append(f'{wx+corner} = {expr}')
    wall_names.append(wx)
    walls_i += 1

circles = []
circle_i = 0
for cx,cy,r in pillars:
    for corner in robot_corners_names:
        cx = 'c'+str(circle_i)+corner    
        circles.append(cx) 
        expr = (circle_collision_expression.format_map({
            'cx': cx,
            'cy': cy,
            'r': r,
            'PosX': corner+'X',
            'PosY': corner+'Y'
        }))
        declarations.append(f'{cx} = {expr}')
    circle_i += 1


output = """\
in Pos
out x
out y
out a
out inside
out seenwalls
out collision
"""
for corner in robot_corners_names:
    output += f'out {corner}X\n'
    output += f'out {corner}Y\n'

for s in chain(streams, circles):
    output+= f'out {s}\n'
    
output += """\
x = List.get(Pos, 0)
y = List.get(Pos, 1)
a = List.get(Pos, 2)
"""

for d in declarations:
    output+= f'{d}\n'

for corner in robot_corners_names:
    output += f'inside{corner} = (({" + ".join(map(lambda x: x+corner, wall_names))}) % 2) == 1\n'


output += f'collision = !({" && ".join(map(lambda x: "inside"+x, robot_corners_names))})'
    
if len(walls) == 0:
    output += '\n'
else:
    output += f' || ({ " || ".join(circles) })\n'

print(output)
