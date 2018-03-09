import json
import time
import paho.mqtt.client as mqtt

mydict = {}
mqtt_host = 'picloud.ourhouse'

def setupMQTTClient(name):
	client = mqtt.Client(name)
	client.connect(mqtt_host)
	client.loop_start()
	client.on_message =  onConfigResponse
	return client

def onConfigResponse(clnt, userdata, msg):
	global mydict
	print("Config received.")
	mydict = json.loads(msg.payload)
	with open('myconfig.json','w') as f:
		json.dump(msg.payload, f)

def getMQTTConfig():
	print("Config not found. Requesting from MQTT.")
	client = setupMQTTClient("masterboard")
	client.subscribe('sun-chaser/config/response/masterboard', qos=2)
	client.publish('sun-chaser/config/request', payload='masterboard', qos=2)
	time.sleep(2)

if __name__ == "__main__":
	try:
		mydict = json.load(open('myconfig.json'))
	except IOError:
		getMQTTConfig()
	print( mydict )
