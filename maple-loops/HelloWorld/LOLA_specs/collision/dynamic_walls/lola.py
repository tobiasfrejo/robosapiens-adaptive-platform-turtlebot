from io import IOBase, StringIO

class LolaStream:
    name: str

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

class LolaSpecification:
    inputs: list[LolaStream]
    outputs: list[LolaStream]
    expressions: list[tuple[LolaStream, str]]

    def __init__(self):
        self.inputs = list()
        self.outputs = list()
        self.expressions = list()

    def add_expression(self, stream:LolaStream, exp: str):
        if stream in self.inputs:
            raise ValueError('Cannot add expressions to input streams')

        if stream not in self.outputs:
            self.outputs.append(stream)
        
        self.expressions.append((stream, exp))

    def get_specification(self, file:IOBase):
        if file.closed:
            raise IOError('File is closed')
        
        if not file.writable():
            raise IOError('File not writable')
        
        for inp in self.inputs:
            file.write(f'in {inp.name}\n')
        for outp in self.outputs:
            file.write(f'out {outp.name}\n')
        for stream, expr in self.expressions:
            file.write(f'{stream.name} = {expr}\n')

    def get_specification_string(self):
        f = StringIO()
        self.get_specification(f)
        f.seek(0)
        return f.read()
    
    def write_specification(self, filename:str):
        with open(filename, 'w') as f:
            self.get_specification(f)
        
def lola_chain(exprs, symbol):
    str_expressions = []
    for exp in exprs:
        if isinstance(exp, LolaStream):
            str_expressions.append(exp.name)
        else:
            str_expressions.append(f'({exp})')

    return f" {symbol} ".join(str_expressions)

def leq(lhs:str, rhs:str):
    return lhs + '<=' + rhs

def gt(lhs:str, rhs:str):
    return f"!({leq(lhs, rhs)})"

def geq(lhs:str, rhs:str):
    return leq(rhs, lhs)

def lt(lhs:str, rhs:str):
    return f"!({leq(rhs, lhs)})"

