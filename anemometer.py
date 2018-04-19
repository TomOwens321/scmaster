import Adafruit_BBIO.GPIO as GPIO
import paho.mqtt.client as mqtt
import json
import time

anemPin = "P9_20"
counter = 0.0
stats = {"maxws": 0.0, "currentspeed": 0.1}

def inc_counter(event):
    global counter
    counter = counter + 1.0
    
def reset_counter():
    global counter
    counter = 0.0

def proc_stats():
    global stats
    currTime = time.ctime()
    rps = counter / 10
    ws  = rps * 1.492
    stats['currentspeed'] = float( str("%.1f" % ws) )
    stats['currenttime'] = currTime
    if (ws > stats['maxws']):
        stats['maxws'] = float( str("%.1f" % ws) )
        stats['maxrpm'] = rps * 60
        stats['maxtime'] = currTime

def print_stats():
    topic = 'sun-chaser/weather/wind'
    logclient = client
    try:
        logclient.publish(topic, payload=json.dumps(stats), qos=0, retain=False)
    except:
        print("Error publishing to MQTT. Attempting to reconnect.")
        logclient.reconnect()
    print( stats )

GPIO.setup(anemPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(anemPin, GPIO.FALLING, callback=inc_counter, bouncetime=0)

client = mqtt.Client()
client.connect('picloud.ourhouse', keepalive=300)

while 1:
    reset_counter()
    time.sleep(10)
    lastspeed = stats['currentspeed']
    proc_stats()
    if (stats['currentspeed'] != lastspeed):
        print_stats()
