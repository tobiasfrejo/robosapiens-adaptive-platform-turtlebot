import json

from rpio.clientLibraries.rpclpy.node import Node, KnowledgeManager, CommunicationManager

def _ensure_publish_key_exist(node, key):
    # You should not have to declare these in the config. Or should you??

    event_key = 'k_' + key
    # TODO: can we do this cleaner?
    if event_key not in node.communication_manager.mqtt_publish_topics_map:
        node.communication_manager.mqtt_publish_topics_map[event_key] = event_key
    return event_key

def write(node:Node, key, value = True):
    event_key = _ensure_publish_key_exist(node, key)
    node.knowledge.write(key, value)
    node.publish_event(event_key, message=json.dumps({"Str": "write"}))

def read(node:Node, key, queueSize = 1):
    event_key = _ensure_publish_key_exist(node, key)
    data = node.knowledge.read(key, queueSize)
    node.publish_event(event_key, message=json.dumps({"Str": "read"}))

    return data
