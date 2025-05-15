import paho.mqtt.client as mqtt
import time

TIMEOUT = 0.05
N = 30
stop = False
i = 0

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
    if message.topic == "/new_data":
        client.publish('SOLClock', '{"Str": "monitor"}')
    elif message.topic == "/Scan":
        client.publish('SOLClock', '{"Str": "scan"}')

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        client.subscribe("/new_data")


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

mqttc.connect("localhost")

try:
    mqttc.loop_start()
    while True:
        time.sleep(TIMEOUT)
        i += 1
        i = i % N
        print('\r' + '#'*i + " "*(N-i),end='')
        mqttc.publish('SOLClock', '{"Str": "timer"}')
    mqttc.loop_forever()
    print(f"Received the following message: {mqttc.user_data_get()}")
except KeyboardInterrupt:
    stop = True
    print('\r'+(''.join([' '*N]))+'\rStopping SOLClock')
finally:
    mqttc.loop_stop()
