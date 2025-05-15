import paho.mqtt.client as mqtt

topics = [
    "telemetry/ghost/pos",
    "lola/ghost.lola/GhostCollision",
    "telemetry/collision2/obstacles"
]

message_counts = {
    t: 0 for t in topics
}

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        for topic in topics:
            client.subscribe(topic)

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    # Be careful, the reason_code_list is only present in MQTTv5.
    # In MQTTv3 it will always be empty
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
    else:
        print(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()

def on_message(client, userdata, message):
    topic = str(message.topic)
    message_counts[topic] += 1

    ESC = '\x1b'

    print(f"{ESC}[{len(topics)}A",end='')
    for topic in topics:
        print(f"{ESC}[2K\r{topic}: {message_counts[topic]}")


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

mqttc.connect("localhost")
try:
    mqttc.loop_forever()
except KeyboardInterrupt:
    pass
finally:
    mqttc.loop_stop()