from glob import glob
from os import path
import time
import paho.mqtt.client as mqtt

W1Path = '/sys/bus/w1/devices/22*'

def w1_therm_scan():
    devs = glob(W1Path)
    # print("Devs Found: {}".format(len(devs)))
    return devs

def read_temperature(dev):
    path = dev + '/w1_slave'
    with open(path) as f:
        data = f.readlines()
    # print( "Data: {}".format(data))
    # print( "Last line: {}".format(data[1]))
    temp = float(data[1].split('=')[1]) / 1000
    # print( "Temperature: {}".format(temp))
    return temp

def publish(dev,temp):
    topic = 'sun-chaser/temps/{}'.format(path.basename(dev))
    client.publish(topic,str(temp),qos=0,retain=True)

client = mqtt.Client()
client.connect('picloud.ourhouse')

while True:
    # print("Scanning for devs....")
    sensors = w1_therm_scan()
    for sensor in sensors:
        temperature = read_temperature(sensor)
        # print("Sensor: {} | Temperature: {}".format(sensor,temperature))
        publish(sensor,temperature)
    time.sleep(15)


