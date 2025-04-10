import lola

spec = lola.LolaSpecification()

x = lola.LolaStream('x_test')
y = lola.LolaStream('y_test')
a = lola.LolaStream('a_test')
b = lola.LolaStream('b_test')

stream_dic = {'x': x, 'y': y, 'angle': a, 'b': b}


exp_x = lola.Expression('List.get(Odometry, 0)')
exp_y = lola.Expression('»x« + 5', stream_dic)
exp_a = lola.Expression('List.get(Odometry, 2)')
exp_b = lola.Expression('»y«+2', stream_dic)


spec.inputs.append(lola.LolaStream('Odometry'))
spec.add_expression(x, exp_x)
spec.add_expression(y, exp_y, keep_on_prune=True)
spec.add_expression(a, exp_a)
spec.add_expression(b, exp_b)

exp = '(((›x‹) * cos(›angle‹)) - ((›y‹) * sin(›angle‹))) + ›y‹' 
exp_test = lola.Expression(exp, stream_dic)

list_exp = exp_test.get_exp_list()
print(list_exp)
for elem in list_exp:
    print(type(elem), elem)
print(exp_test)
print()

test = lola.LolaStream('test')
spec.add_expression(test, exp_test, keep_on_prune=True)
print("======START SPEC========")
print(spec.get_specification_string())
print("====== SPEC END ========")
print()

exp2 = '(›x‹) + ((›y‹) * sin(›angle‹))' 

exp_test2 = lola.Expression(exp2, stream_dic)

chained = lola.lola_chain([exp_test, exp_test2], '&&')
print(chained)
print()

print("======Dependency Graph========")
spec.print_dependency_graph()
print()

spec.collapse_expression(test)
print("======Collapsed Expression========")
print(spec.expressions[test])
print()

print("======Collasped Graph========")
spec.print_dependency_graph()
print()
spec.prune()

print("======Pruned Graph========")
spec.print_dependency_graph()
print()

print("======START SPEC========")
print(spec.get_specification_string())
print("====== SPEC END ========")



empty = lola.Expression('')
print(empty.get_exp_list())
print(empty)