import re 

def ensure_publish_key_exist(node, key, make_trustworthiness_checker_safe:bool=True):
    # You should not have to declare these in the config. Or should you??

    if make_trustworthiness_checker_safe:
        event_key = trustworthiness_checker_safe_key(key)
    else:
        event_key = key

    # TODO: can we do this cleaner?
    if event_key not in node.communication_manager.mqtt_publish_topics_map:
        node.communication_manager.mqtt_publish_topics_map[event_key] = event_key
    return event_key

def trustworthiness_checker_safe_key(key:str):
    return re.sub(r'[^a-zA-Z0-9]', '', re.sub(r'_([a-z])', lambda match: match.group(1).upper(), key))
