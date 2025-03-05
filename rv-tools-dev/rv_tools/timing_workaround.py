import json
from rpio.clientLibraries.rpclpy.node import Node, KnowledgeManager, CommunicationManager
from rv_tools.events import ensure_publish_key_exist

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
