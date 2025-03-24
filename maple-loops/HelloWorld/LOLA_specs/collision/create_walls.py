import numpy as np
# Scaled to keep precision as ints
walls = np.array([
    (( 10,-10), (-10,-10)),
    ((-10,-10), (-10, 10)),
    ((-10, 10), ( 10, 10)),
    (( 10, 10), ( 10,-10)),
])
walls *= 1000



expression = "!((PosX * ({a}) + PosY * ({b}) + ({c})) <= 0)"


expressions = []
for A, B in walls:
    Ax, Ay = A
    Bx, By = B
    c1 = By-Ay
    c2 = Ax-Bx
    c3 = Ay*Bx - Ax*By

    expressions.append(expression.format_map({
        'a':c1, 
        'b':c2, 
        'c':c3}))

print('inside = ' + ' && '.join(expressions))