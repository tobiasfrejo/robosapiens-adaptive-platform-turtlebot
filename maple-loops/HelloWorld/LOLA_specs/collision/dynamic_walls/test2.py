import lola

spec = lola.LolaSpecification()

x = lola.LolaStream('x_test')
y = lola.LolaStream('y_test')
a = lola.LolaStream('a_test')
b = lola.LolaStream('b_test')

stream_dic = {'x': x, 'y': y, 'angle': a}

exp_x = lola.Expression('List.get(Odometry, 0)')
exp_y = lola.Expression('›x‹ + 5', stream_dic)
exp_a = lola.Expression('List.get(Odometry, 2)')


spec.inputs.append(lola.LolaStream('Odometry'))
spec.add_expression(x, exp_x)
spec.add_expression(y, exp_y)

spec.add_expression(a, exp_a)

exp = '(((›x‹) * cos(›angle‹)) - ((›y‹) * sin(›angle‹))) + ›y‹' 

exp_test = lola.Expression(exp, stream_dic)

list_exp = exp_test.get_exp_list()
print(list_exp)
print(exp_test)
print()

test = lola.LolaStream('test')
spec.add_expression(test, exp_test)
print("======START SPEC========")
print(spec.get_specification_string())
print("====== SPEC END ========")
print()

exp2 = '(›x‹) + ((›y‹) * sin(›angle‹))' 

exp_test2 = lola.Expression(exp2, stream_dic)

chained = lola.lola_chain([exp_test, exp_test2], '&&')
print(chained)
print()

collapsed_test, collapsed_streams = spec.collapse_expression(test)
print("======Collapse========")
print(collapsed_test)
print(collapsed_streams)

spec2 = lola.LolaSpecification()
spec2.inputs = spec.inputs.copy()
spec_outputs = set(spec.outputs)
spec2_outputs = spec_outputs - collapsed_streams
