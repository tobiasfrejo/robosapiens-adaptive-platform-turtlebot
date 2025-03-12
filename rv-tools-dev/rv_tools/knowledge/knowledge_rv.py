import json
import re

from rv_tools.events import ensure_publish_key_exist
from rv_tools.timing_workaround import trustworthiness_output
from rv_tools.constants import *
from rpio.clientLibraries.rpclpy.node import Node, KnowledgeManager, CommunicationManager

def write(node:Node, key:str, value = True):
    event_key = ensure_publish_key_exist(node, 'k_' + key)
    node.knowledge.write(key, value)
    node.publish_event(event_key, message=json.dumps({"Str": "write"}))
    node.publish_event(ensure_publish_key_exist(node, node.__class__.__name__ + WRITING_PHASE), message=json.dumps({"Str": "write"}))
    # node.publish_event(ensure_publish_key_exist(node, 'any_knowledge_write', False), message=json.dumps({'Str':key}))

def read(node:Node, key, queueSize = 1):
    event_key = ensure_publish_key_exist(node, 'k_' + key)
    data = node.knowledge.read(key, queueSize)
    node.publish_event(event_key, message=json.dumps({"Str": "read"}))
    # node.publish_event(ensure_publish_key_exist(node, 'any_knowledge_read', False), message=json.dumps({'Str':key}))

    return data
