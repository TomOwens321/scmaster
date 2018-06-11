import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC  as ADC
import paho.mqtt.client as mqtt
import json
import time

anemPin = "P9_20"
dirPin  = "P9_36"
counter = 0.0
stats = {"maxws": 0.0, "currentspeed": 0.1, "direction": "N"}
last_time = time.time()

def inc_counter(event):
    global counter
    counter = counter + 1.0
    # gust_sensor()
    
def reset_counter():
    global counter
    counter = 0.0
    
def gust_sensor():
    global last_time, stats
    now_time = time.time()
    period = now_time - last_time
    last_time = now_time
    gust = ((1/period) * 1.492) / 1000
    print(1/gust)
    if gust > stats['gust']:
        stats['gust'] = float( str("%.1f" % gust) )


def proc_stats():
    global stats
    currTime = time.ctime()
    rps = counter / 10
    ws  = rps * 1.492
    stats['currentspeed'] = float( str("%.1f" % ws) )
    stats['currenttime'] = currTime
    if (ws > stats['maxws']):
        stats['maxws'] = float( str("%.1f" % ws) )
        # stats['maxrpm'] = rps * 60
        stats['maxtime'] = currTime
    direction = ADC.read(dirPin) * 3.3
    stats['direction'] = direction_text(direction)

def print_stats():
    global stats
    topic = 'sun-chaser/weather/wind'
    logclient = client
    try:
        logclient.publish(topic, payload=json.dumps(stats), qos=0, retain=False)
    except:
        print("Error publishing to MQTT. Attempting to reconnect.")
        logclient.reconnect()
    print( stats )
    
def direction_text( dir ):
    dir = int(dir * 100)
    if dir in range(239, 260):
        return "N  "
    if dir in range(111, 140):
        return "NNE"
    if dir in range(140, 171):
        return "NE "
    if dir in range(24, 28):
        return "ENE"
    if dir in range(28, 35):
        return "E  "
    if dir in range(1, 24):
        return "ESE"
    if dir in range(50, 69):
        return "SE "
    if dir in range(35, 50):
        return "SSE"
    if dir in range(85, 111):
        return "S  "
    if dir in range(69, 85):
        return "SSW"
    if dir in range(198, 214):
        return "SW "
    if dir in range(171, 198):
        return "WSW"
    if dir in range(295, 400):
        return "W  "
    if dir in range(260, 276):
        return "WNW"
    if dir in range(276, 295):
        return "NW "
    if dir in range(214, 239):
        return "NNW"
    return str(dir)
    

GPIO.setup(anemPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(anemPin, GPIO.FALLING, callback=inc_counter, bouncetime=0)
ADC.setup()

client = mqtt.Client()
client.connect('picloud.ourhouse', keepalive=3000)

while 1:
    reset_counter()
    time.sleep(10)
    lastspeed = stats['currentspeed']
    lastdir   = stats['direction']
    proc_stats()
    if ((stats['currentspeed'] != lastspeed) or (stats['direction'] != lastdir)):
        print_stats()
