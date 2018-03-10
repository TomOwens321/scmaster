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
		json.dump(mydict, f)

def getMQTTConfig():
	print("Config not found. Requesting from MQTT.")
	client = setupMQTTClient("masterboard")
	client.subscribe('sun-chaser/config/response/slaveboard', qos=2)
	client.publish('sun-chaser/config/request', payload='slaveboard', qos=2)
	time.sleep(2)

def getConfig():
	try:
		with open('myconfig.json','r') as f:
			mydict = json.load(f)
	except IOError:
		getMQTTConfig()
		with open('myconfig.json','r') as f:
			mydict = json.load(f)
	return mydict

def setConfig(myconfig):
	with open('myconfig.json','w') as f:
		json.dump(myconfig, f)

if __name__ == "__main__":
	try:
		with open('myconfig.json','r') as f:
			mydict = json.load(f)
	except IOError:
		getMQTTConfig()
	print( mydict )
