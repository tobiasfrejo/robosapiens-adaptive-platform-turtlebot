import json
from rpio.clientLibraries.rpclpy.node import Node, KnowledgeManager, CommunicationManager
from rv_tools.events import ensure_publish_key_exist
from rv_tools import constants

import logging
logger = logging.getLogger(__name__)


def twc_helper(twn:Node, source_node: str, event:str, extra:str=''):
    short_name = source_node.lower()[0]

    messages = {
        constants.ATOMICITY: f'{event}_{short_name}{extra}',
        source_node + constants.WRITING_PHASE: f'{event}_{extra}' if extra else f'{event}'
    }

    if event == 'start':
        pass
    elif event == 'end':
        messages.update({
            constants.MAPLE: f'{short_name}{extra}'
        })
        if source_node == 'Monitor':
           messages.update({
            constants.SCANTRIGGER: f'{short_name}{extra}'
        }) 
    else:
        raise ValueError('event must be "start" or "end"')

    for stream_name, value in messages.items():
        key = ensure_publish_key_exist(twn, stream_name)
        msg = json.dumps({"Str": value})
        twn.publish_event(key, message=msg)
