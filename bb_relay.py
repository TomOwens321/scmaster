import time
import Adafruit_BBIO.GPIO as GPIO
import paho.mqtt.client as mqtt
from threading import Event, Thread
import config

def call_repeatedly(interval, func, offset, *args):
    stopped = Event()
    def loop():
        while not stopped.wait((interval * 60) - offset):
            func(*args)
    Thread(target=loop).start()    
    return stopped.set

def pulse(relay):
    pin = relay['pin']
    ontime = int(relay['duration'])
    print("Watering {} for {} seconds.".format(relay['name'],ontime))
    GPIO.output(pin, GPIO.LOW)
    time.sleep(ontime)
    GPIO.output(pin, GPIO.HIGH)
    print("Finished watering {}.".format(relay['name']))

def mqtt_message(client, userdata, message):
    if ('config' in message.topic):
        newMQTTConfig(message)
    print("MQTT Message Received.")
    relay = getRelayFromTopic(message.topic)
    if relay == None:
        print("Relay not found in {}".format(message.topic))
        return
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
    if 'moisture' in str(message.topic):
        moisture = int(message.payload)
        print("Setting {} Moisture to: {}".format(relay['name'],moisture))
        relay['moisture'] = str(moisture)
    if 'now' in str(message.topic):
        print("Someone pressed The Button for {}.".format(relay['name']))
        pulse(relay)
    if 'control' in str(message.topic):
        reset_timer(interval, duration, relay)
    saveConfig()

def newMQTTConfig(message):
    global myconfig
    if (myconfig['name'] in message.topic):
        print("Saving new configuration.")
        with open('myconfig.json', 'w') as f:
            f.write(message.payload)
            f.close()
        myconfig = config.getConfig()

def saveConfig():
    print(myconfig)
    config.setConfig(myconfig)

def getRelayFromTopic(topic):
    for relay in myconfig['relays']:
        if relay['name'] in topic:
            return relay
    return None

def reset_timer(interval, duration, relay):
    global cfcs
    cfcs[relay['name']]()
    time.sleep(1)
    cfcs[relay['name']] = call_repeatedly(interval, pulse, duration, relay)

#GPIO.setup(relay, GPIO.OUT)

myconfig = config.getConfig()
print(myconfig)

client = mqtt.Client()
client.connect('picloud.ourhouse')
client.on_message = mqtt_message
client.loop_start()
client.subscribe('sun-chaser/control/{}/#'.format(myconfig['name']), qos=2)
client.subscribe('sun-chaser/config/{}'.format(myconfig['name']), qos=1)

cfcs = {}

# Start Threads
for relay in myconfig['relays']:
    GPIO.setup(relay['pin'], GPIO.OUT)
    GPIO.output(relay['pin'], GPIO.HIGH)
    interval = int(relay["interval"])
    duration = int(relay['duration'])
    cfcs[relay['name']] = call_repeatedly(interval, pulse, duration, relay)

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("Cleaning and Exiting.")
    client.disconnect()
    client.loop_stop()
    for relay in cfcs.values():
        relay()
