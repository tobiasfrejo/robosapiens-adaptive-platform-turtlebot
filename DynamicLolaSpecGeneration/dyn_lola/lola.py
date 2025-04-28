from io import IOBase, StringIO
import re
from typing import Union, Iterable
import networkx as nx

Expression_type = Union["Expression", str, "LolaStream"]
class LolaStream:
    name: str

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"›{self.name}‹"
        return self.name

    def __str__(self):
        return self.name
        # return self.__repr__()

class Expression:
    Expression_component_types = str | LolaStream
    # stream: LolaStream
    exp: list[Expression_component_types]
    active_dependencies : set[LolaStream]
    
    def __init__(self, exp: str | Iterable[Expression_type]=None, stream_dic: dict[str, LolaStream]=None):
        # input expample: 
        # exp = '(((‹x›) * cos(‹angle›)) - ((‹y›) * sin(‹angle›))) + ‹center_of_rotation[0]›' 
        # stream_dic = {'x': LolaStream('x'), etc} 
        self.exp = []
        self.active_dependencies = set()
        if exp is None:
            return
            
        elif isinstance(exp, str):
            self.__string_init_(exp, stream_dic)
        
        elif isinstance(exp, Iterable):
            for e in exp:
                self.append(e)   
        
    def __string_init_(self, exp: str, stream_dic: dict[str, LolaStream]=None):
        substrings_exp_types = filter(lambda x: x is not None, re.split(r'(›[^‹]+‹)|(»[^«]+«)', exp))
        
        for substr in substrings_exp_types:
            if (substr.startswith('›') and substr.endswith('‹')) or (substr.startswith('»') and substr.endswith('«')):
                key = substr[1:-1]
                if stream_dic is None:
                    raise ValueError('To use LOLA streams in an expression a stream dictionary must be provided')
                if key in stream_dic:
                    stream = stream_dic[key]
                    self.exp.append(stream)
                    if isinstance(stream, LolaStream):
                        self.active_dependencies.add(stream)
                else:
                    raise ValueError(f'Key {key} not found in stream dictionary')
            else:
                if substr:
                    self.exp.append(substr)
        
    def append(self, to_append: Union["Expression", str, LolaStream]):
        if isinstance(to_append, Expression):
            self.exp.append("(")
            self.exp += to_append.exp
            self.exp.append(")")
            self.active_dependencies.update(to_append.active_dependencies)
        elif isinstance(to_append, LolaStream):
            self.exp.append(to_append)
            self.active_dependencies.add(to_append)
        else:
            self.exp.append(to_append)
            
    def copy(self):
        new_exp = Expression('')
        new_exp.exp = self.exp.copy()
        new_exp.active_dependencies = self.active_dependencies.copy()
        return new_exp
    
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
    dependency_graph: nx.DiGraph
    

    def __init__(self):
        self.inputs = list()
        self.outputs = list()
        self.expressions = dict()
        self.dependency_graph = nx.DiGraph()

    def add_expression(self, stream:LolaStream, exp: Expression, keep_on_prune: bool = False):
        if stream in self.inputs:
            raise ValueError('Cannot add expressions to input streams')

        if stream not in self.outputs:
            self.outputs.append(stream)
            # If output_stream keep in spec even if all other nodes no longer depend on due to collapsing
        self.dependency_graph.add_node(stream, output_stream=keep_on_prune)
            
        self.expressions[stream] = exp
        
        dependencies = exp.active_dependencies
        for dep_stream in dependencies:
            self.dependency_graph.add_edge(stream, dep_stream)
        
    def collapse_expression_recur(self, stream : LolaStream):
        if stream in self.inputs:
            x = str(stream)
            return Expression(x), set()
        if stream not in self.expressions:
            raise ValueError(f'No expression found for {stream}')
        
        collapsed_streams = set()
        exp = self.expressions[stream]
        if not isinstance(exp, Expression):
            exp = Expression(str(exp))
        exp_list = exp.get_exp_list()
        collapsed = Expression()
        for sub_exp in exp_list:
            if isinstance(sub_exp, LolaStream):
                if sub_exp not in self.expressions and sub_exp not in self.inputs:
                    raise ValueError(f'No expression found for {sub_exp} in stream {stream}')
                if not self.dependency_graph.nodes[sub_exp].get('output_stream', False):
                    collapsed_sub_exp,_ = self.collapse_expression_recur(sub_exp)                
                    collapsed.append(collapsed_sub_exp)
                    collapsed_streams.add(sub_exp)
                else: 
                    collapsed.append(sub_exp)
            else:
                collapsed.append(sub_exp)
        return collapsed, collapsed_streams # expression
        
    def collapse_expression(self, stream: LolaStream):
        collapsed, collapsed_streams = self.collapse_expression_recur(stream)

        self.expressions[stream] = collapsed
        for no_longer_depend in collapsed_streams:
                self.dependency_graph.remove_edge(stream, no_longer_depend)
        for new_dep in collapsed.active_dependencies:
            if new_dep not in collapsed_streams:
                self.dependency_graph.add_edge(stream, new_dep)
      
    def prune(self):
        def root_node_filter(in_degree_view):
            node, in_degree = in_degree_view
            return in_degree == 0 
        
        root_streams = list(map(lambda x: x[0], filter(root_node_filter, self.dependency_graph.in_degree())))
        
        def prune_traverse(stream):
            is_output_stream = self.dependency_graph.nodes[stream].get('output_stream', False)
            is_input_stream = stream in self.inputs
            if is_output_stream or is_input_stream:
                return
            for _, dest_node in list(self.dependency_graph.out_edges(stream)): 
                prune_traverse(dest_node)
            self.dependency_graph.remove_node(stream)
            self.expressions.pop(stream, None)
            self.outputs.remove(stream)
        
        for stream in root_streams:
            prune_traverse(stream)

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
    
    def _print_list(self, lst: list, name: str):
        print(f"{name}:")
        for item in lst:
            print(' '*4, end='')
            print(item)
    
    def print_dependency_graph(self):
        self._print_list(self.dependency_graph.nodes(), 'Nodes')
        self._print_list(self.dependency_graph.edges(), 'Edges')
        self._print_list(self.dependency_graph.in_degree(), 'In Degrees')
        self._print_list(self.dependency_graph.out_degree(), 'Out Degrees')
    
        
def lola_chain(exprs : list[Expression_type], symbol: str): #TODO: dict expression fucked this up(?)
    l = len(exprs)
    new_expression = Expression('')
    #stream_dict = dict()
    for i in range(l):
        exp = exprs[i]
        if isinstance(exp, str):
            if exp:
                new_expression.append(f"({exp})")
        else:
            new_expression.append(exp)
        if i < l - 1:
            new_expression.append(f" {symbol} ")        
    return new_expression



def leq(lhs:Expression_type, rhs:Expression_type):
    return lola_chain([lhs, rhs], '<=')

def gt(lhs:Expression_type, rhs:Expression_type):
    return lola_chain([lhs, rhs], '>')

def geq(lhs:Expression_type, rhs:Expression_type):
    return lola_chain([lhs, rhs], '>=')

def lt(lhs:Expression_type, rhs:Expression_type):
    return lola_chain([lhs, rhs], '<')

def lnot(exp:Expression_type):
    new_expression = Expression('!(')
    new_expression.append(exp)
    new_expression.append(")")
    return new_expression