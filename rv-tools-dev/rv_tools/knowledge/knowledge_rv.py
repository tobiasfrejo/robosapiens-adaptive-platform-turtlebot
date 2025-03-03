import json
import re

from rpio.clientLibraries.rpclpy.node import Node, KnowledgeManager, CommunicationManager

def _ensure_publish_key_exist(node, key, make_trustworthiness_checker_safe:bool=True):
    # You should not have to declare these in the config. Or should you??

    if make_trustworthiness_checker_safe:
        event_key = _trustworthiness_checker_safe_key('k_' + key)
    else:
        event_key = key

    # TODO: can we do this cleaner?
    if event_key not in node.communication_manager.mqtt_publish_topics_map:
        node.communication_manager.mqtt_publish_topics_map[event_key] = event_key
    return event_key

def _trustworthiness_checker_safe_key(key:str):
    return re.sub(r'[^a-zA-Z]', '', re.sub(r'_([a-z])', lambda match: match.group(1).upper(), key))

def write(node:Node, key:str, value = True):
    event_key = _ensure_publish_key_exist(node, key)
    node.knowledge.write(key, value)
    node.publish_event(event_key, message=json.dumps({"Str": "write"}))
    node.publish_event(_ensure_publish_key_exist(node, 'any_knowledge_write', False), message=json.dumps({'Str':key}))

def read(node:Node, key, queueSize = 1):
    event_key = _ensure_publish_key_exist(node, key)
    data = node.knowledge.read(key, queueSize)
    node.publish_event(event_key, message=json.dumps({"Str": "read"}))
    node.publish_event(_ensure_publish_key_exist(node, 'any_knowledge_read', False), message=json.dumps({'Str':key}))

    return data
