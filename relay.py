import time
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from threading import Event, Thread
import config
import json

def call_repeatedly(interval, func, offset, *args):
    stopped = Event()
    def loop():
        while not stopped.wait(interval - offset): # the first call is in `interval` secs
            func(*args)
    Thread(target=loop).start()    
    return stopped.set

def pulse(relay):
    pin = int(relay['pin'])
    ontime = int(relay['duration'])
    print("Watering {} for {} seconds.".format(relay['name'],ontime))
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(ontime)
    GPIO.output(pin, GPIO.LOW)
    print("Finished watering {}.".format(relay['name']))

def mqtt_message(client, userdata, message):
    print("MQTT Message Received.")
    relay = getRelayFromTopic(message.topic)
    duration = int(relay['duration'])
    interval = int(relay['interval'])
    if 'duration' in str(message.topic):
        duration = int(message.payload)
        print("Setting {} Duration to: {}".format(relay['name'],duration))
        relay['duration'] = str(duration)
    if 'interval' in str(message.topic):
        interval = int(message.payload)
        print("Setting {} Interval to: {}".format(relay['name'],interval))
        relay['interval'] = str(interval)
    if 'control' in str(message.topic):
        reset_timer(interval, duration, relay)

def getRelayFromTopic(topic):
    for relay in myconfig['relays']:
        if relay['name'] in topic:
            return relay
    return None

def reset_timer(interval, duration, relay):
    relay['cfc']()
    time.sleep(1)
    relay['cfc'] = call_repeatedly(interval, pulse, duration, relay)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#GPIO.setup(relay, GPIO.OUT)

myconfig = json.loads(config.getConfig())
print(myconfig)

client = mqtt.Client()
client.connect('picloud.ourhouse')
client.on_message = mqtt_message
client.loop_start()
client.subscribe('sun-chaser/control/{}/#'.format(myconfig['name']), qos=2)

# Start Threads
for relay in myconfig['relays']:
    GPIO.setup(int(relay['pin']), GPIO.OUT)
    interval = int(relay["interval"])
    duration = int(relay['duration'])
    relay['cfc'] = call_repeatedly(interval, pulse, duration, relay)

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("Cleaning and Exiting.")
    client.disconnect()
    client.loop_stop()
    for relay in myconfig['relays']:
        relay['cfc']()