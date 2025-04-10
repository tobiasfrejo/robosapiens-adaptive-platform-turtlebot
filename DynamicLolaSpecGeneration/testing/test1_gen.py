from dyn_lola.lola import LolaStream, Expression, LolaSpecification

spec = LolaSpecification()

spec.inputs.append(LolaStream('a'))
spec.inputs.append(LolaStream('b'))
spec.inputs.append(LolaStream('c'))

x = LolaStream('x')
y = LolaStream('y')
z = LolaStream('z')

stream_dic = {'x': x, 'y': y, 'z': z}

exp_x = Expression('2 * b')
exp_y = Expression('›x‹ + a', stream_dic)  
exp_z = Expression('c + ›x‹ * ›y‹', stream_dic) 

spec.add_expression(x, exp_x)
spec.add_expression(y, exp_y)
spec.add_expression(z, exp_z, keep_on_prune=True)

spec.write_specification('test1_full.lola')
print("======FULL GRAPH========")
spec.print_dependency_graph()

spec.collapse_expression(z)
spec.prune()
spec.write_specification('test1_collapsed.lola')
print("======COLLASPED GRAPH========")
spec.print_dependency_graph()

