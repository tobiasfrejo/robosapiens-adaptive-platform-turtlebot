import json
from rpio.clientLibraries.rpclpy.node import Node, KnowledgeManager, CommunicationManager
from rv_tools.events import ensure_publish_key_exist
from rv_tools import constants

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def trustworthiness_output(node:Node, stream_name:str, value:str):
    key = ensure_publish_key_exist(node, stream_name)
    msg = json.dumps({"Str": value})
    node.publish_event(key, message=msg)
    print(f'Published to trustworthiness checker: {key}: {msg} -- for {node.__class__.__name__}')

def trustworthiness_outputs(node:Node, pairs:dict[str,str]):
    for k,v in pairs.items():
        trustworthiness_output(node, k, v)

def trustworthiness_output2(node:Node, event:str, extra:str=''):
    name = node.__class__.__name__
    short_name = name.lower()[0]

    messages = {
        constants.ATOMICITY: f'{event}_{short_name}{extra}',
        node.__class__.__name__ + constants.WRITING_PHASE: event
    }

    if event == 'start':
        pass
    elif event == 'end':
        messages.update({
            constants.MAPLE: f'{short_name}{extra}'
        })
    else:
        raise ValueError('event must be "start" or "end"')
    trustworthiness_outputs(node, messages)
