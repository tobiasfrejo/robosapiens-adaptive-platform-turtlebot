from warnings import warn
import numpy as np
from itertools import chain
# Scaled to keep precision as ints

corners = np.array([
    (3,3),
    (-2,6),
    (-5,2),
    (-8,-1),
    (-8,-6),
    (1,-4),
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
        warn(f'({i}, {j}): {corners[i]}, {corners[j]}')
    walls = np.array(walls)
    return walls

walls = np.concat((
    connect_polygon(corners),
    # connect_polygon(obstacle1)
))
warn(str(len(walls)))

walls *= 1000

# (Cx, Cy, R)
pillars = np.array([
    # ( 1,  2,  1)
])

pillars *= 1000

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
   (((PosX - {cx}) * (PosX - {cx})) \
  + ((PosY - {cy}) * (PosY - {cy}))) \
    <= ({r} * {r})\
)'''

"""
https://wrfranklin.org/Research/Short_Notes/pnpoly.html

(Ay > Py  !=  By > Py)
&&  (Px  <  (Bx-Ax) * (Py-Ay) / (By-Ay) + Ax)
"""
expression = """\
if !(\
 !({ay} <= PosY) == !({by} <= PosY)\
) && !(\
 (({a}) * ((PosY) - ({ay})) + ({ax1})) <= (PosX * 1000)) \
then 1 \
else 0 \
"""


expressions = []
for A, B in walls:
    Ax, Ay = A
    Bx, By = B

    if Ay == By:
        continue

    expressions.append(expression.format_map({
        'a':int((Bx-Ax)/(By-Ay)*1000),
        'ax1': int(Ax*1000),
        'ay': Ay,
        'ay1': int(Ay*1000),
        'bx': Bx,
        'by': By
    }))

circle_expressions = []
for cx,cy,r in pillars:
    circle_expressions.append(circle_collision_expression.format_map({
        'cx': cx,
        'cy': cy,
        'r': r
    }))

streams = []
declarations = []

for n,expr in enumerate(expressions):
    wx = 'w'+str(n)
    streams.append(wx)
    declarations.append(f'{wx} = {expr}')

circles = []
for n,expr in enumerate(circle_expressions):
    cx = 'c'+str(n)
    circles.append(cx)
    declarations.append(f'{cx} = {expr}')

output = """\
in Pos
out PosX
out PosY
out inside
out seenwalls
out collision
"""
for s in chain(streams, circles):
    output+= f'out {s}\n'
output += """\
PosX = List.get(Pos, 0)
PosY = List.get(Pos, 1)
"""
for d in declarations:
    output+= f'{d}\n'

output += f'seenwalls = ({" + ".join(streams)})\n'
output += 'inside = (seenwalls - ((seenwalls / 2) * 2)) == 1\n'
if len(circles) == 0:
    output += 'collision = !inside'
else:
    output += f'collision = !inside && !({ " || ".join(circles) })\n'

print(output)
