from io import IOBase, StringIO
import re

class LolaStream:
    name: str

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"›{self.name}‹"

    def __str__(self):
        return self.__repr__()
    


class Expression:
    Expression_component_types = str | LolaStream
    # stream: LolaStream
    exp: list[Expression_component_types]
    
    def __init__(self, exp: str, stream_dic: dict[str, LolaStream]=None):
        # input expample: 
        # exp = '(((‹x›) * cos(‹angle›)) - ((‹y›) * sin(‹angle›))) + ‹center_of_rotation[0]›' 
        # stream_dic = {'x': LolaStream('x'), etc} 
        self.exp = []
        substrings_exp_types = re.split(r'(›[^‹]+‹)', exp)
        
        for substr in substrings_exp_types:
            if substr.startswith('›') and substr.endswith('‹'):
                key = substr[1:-1]
                if stream_dic is None:
                    raise ValueError('To use LOLA streams in an expression a stream dictionary must be provided')
                if key in stream_dic:
                    self.exp.append(stream_dic[key])
                else:
                    raise ValueError(f'Key {key} not found in stream dictionary')
            else:
                if substr:
                    self.exp.append(substr)
        
        
    
    def get_exp_list(self):
        """
        Returns the expression as a list of strings and LolaStreams
        """
        return self.exp

    def __repr__(self):
        return ''.join(str(e) for e in self.exp)
        
    def __str__(self):
        return str(self.__repr__())    
        
     
        
        
    
class LolaSpecification:
    inputs: list[LolaStream]
    outputs: list[LolaStream]
    expressions: dict[LolaStream, Expression]
    

    def __init__(self):
        self.inputs = list()
        self.outputs = list()
        self.expressions = dict()

    def add_expression(self, stream:LolaStream, exp: Expression):
        if stream in self.inputs:
            raise ValueError('Cannot add expressions to input streams')

        if stream not in self.outputs:
            self.outputs.append(stream)
        
        self.expressions[stream] = exp
        
    def collapse_expression(self, stream : LolaStream):
        if stream not in self.expressions:
            raise ValueError(f'No expression found for {stream}')
        
        collapsed_streams = set()
        collapsed = []
        exp_list = self.expressions[stream].get_exp_list()
        for sub_exp in exp_list:
            if isinstance(sub_exp, LolaStream):
                if sub_exp not in self.expressions:
                    raise ValueError(f'No expression found for substream {stream}')
                collapsed_sub_exp, sub_streams = self.collapse_expression(sub_exp)
                collapsed_streams.update(sub_streams, {sub_exp})
                collapsed.append(f'({collapsed_sub_exp})')
            elif isinstance(sub_exp, str):
                collapsed.append(sub_exp)
            else:
                raise TypeError('Sub expression is not of type LolaStream or str')
        
        return ''.join(str(e) for e in collapsed), collapsed_streams

    def get_specification(self, file:IOBase):
        if file.closed:
            raise IOError('File is closed')
        
        if not file.writable():
            raise IOError('File not writable')
        
        for inp in self.inputs:
            file.write(f'in {inp.name}\n')
        for outp in self.outputs:
            file.write(f'out {outp.name}\n')
        for stream, expr in self.expressions.items(): 
            file.write(f'{stream.name} = {expr}\n')

    def get_specification_string(self):
        f = StringIO()
        self.get_specification(f)
        f.seek(0)
        return f.read()
    
    def write_specification(self, filename:str):
        with open(filename, 'w') as f:
            self.get_specification(f)
        
def lola_chain(exprs, symbol): #TODO: dict expression fucked this up(?)
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

