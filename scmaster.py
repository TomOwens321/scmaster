import json
import time
import paho.mqtt.client as mqtt

mqtt_host = 'picloud.ourhouse'
configs_file = 'configs.json'

def readConfigs(fname):
    try:
        configs = json.load(open(fname))
    except IOError:
        print("Unable to read configs.json")
        return {}
    return configs

def onConfigRequest(clnt, userdata, msg):
    requester = msg.payload
    print("MQTT config request recieved from: {}".format(requester))
    conf = findConfig(requester)
    if conf != None:
        sendConfig(requester, conf)
    else:
        print("Unable to find config for {}".format(requester))

def findConfig(requester):
    newconf = None
    configs = readConfigs(configs_file)
    for dev in configs['devs']:
        if dev['name'] == requester:
            newconf = dev
            print( "Found {} in data table.".format(dev['name']) )
            break
    return newconf

def sendConfig(requestor, conf):
    global client
    topic = 'sun-chaser/config/response/{}'.format(requestor)
    client.publish(topic, payload=json.dumps(conf), qos=2, retain=False)
    
configs = readConfigs(configs_file)

client = mqtt.Client("SCMaster")
client.connect(mqtt_host)
client.loop_start()
client.on_message =  onConfigRequest
client.subscribe('sun-chaser/config/request', qos=2)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping.")
    client.disconnect()
    client.loop_stop()

#client.publish('sun-chaser/json', payload=json.dumps(msgjson), qos=0, retain=False)