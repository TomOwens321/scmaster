import time
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC  as ADC
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
    mqtt_log("Watering {} for {} seconds.".format(relay['name'],ontime))
    GPIO.output(pin, GPIO.LOW)
    time.sleep(ontime)
    GPIO.output(pin, GPIO.HIGH)
    mqtt_log("Finished watering {}.".format(relay['name']))
    mqtt_status(relay)

def mqtt_log(message):
    topic = "sun-chaser/logs/relay"
    payload = "[{}] Relay : {}".format(time.asctime(), message)
    logclient = client
    logclient.publish(topic, payload=payload, qos=0, retain=False)
    print(payload)

def mqtt_status(relay):
    currenttime = int(time.time())
    nexttime = (currenttime - int(relay['duration'])) + (int(relay['interval']) * 60)
    message = ("{}".format(time.ctime(nexttime)))
    topic = "sun-chaser/status/relay/{}/next".format(relay['name'])
    payload = "{}".format(message)
    logclient = client
    logclient.publish(topic, payload=payload, qos=0, retain=False)
    print(payload)

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

def checkMoisture():
    for relay in myconfig['relays']:
        moist = int( ADC.read(relay['senspin']) * 1000 )
        if (moist < int( relay['moisture'] )):
            mqtt_log("Zone {} moisture is below the threshold.".format(relay['name']))
            pulse(relay)
        else:
            mqtt_log("Zone {} moisture: {}".format(relay['name'], moist))
        
#GPIO.setup(relay, GPIO.OUT)

ADC.setup()

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
    print("Setting up {}".format(relay['name']))
    GPIO.setup(relay['pin'], GPIO.OUT)
    GPIO.output(relay['pin'], GPIO.HIGH)
    interval = int(relay["interval"])
    duration = int(relay['duration'])
    cfcs[relay['name']] = call_repeatedly(interval, pulse, duration, relay)

try:
    while True:
        checkMoisture()
        time.sleep(600)
except KeyboardInterrupt:
    print("Cleaning and Exiting.")
    client.disconnect()
    client.loop_stop()
    for relay in cfcs.values():
        relay()
