#!/usr/bin/env python3

import json
import logging
import datetime
import requests

LOG_LEVEL = 1
logging.basicConfig(format='%(asctime)-15s [%(levelname)s] %(message)s', level=LOG_LEVEL)


H = 'pve3.ad.ibbr.umd.edu'
U = 'monitoring@pve'
P = 'monitoring'

client=requests.session()

URL="https://pve3.ad.ibbr.umd.edu:8006/api2/json/access/ticket"
auth_response = client.post(URL, data={'username':U, 'password':P})

try:
    r = json.loads(auth_response.text)
except:
    print("Aiiee")


ticket = r['data']['ticket']
csrf   = r['data']['CSRFPreventionToken']

cookies = {
    'PVEAuthCookie': ticket,
}



# GET NODES
nodes = client.get('https://pve3.ad.ibbr.umd.edu:8006/api2/json/nodes/', cookies={'PVEAuthCookie': ticket})

try:
    fname = "nodes-{}.json".format(datetime.datetime.now().strftime('%Y%m%d-%H%M'))
    fp = open(fname,mode='w')
except:
    print("Aiiee 2")

fp.write(json.dumps(json.loads(nodes.text), sort_keys=True, indent=4 ))
fp.close()

# GET VMs
vms = client.get('https://pve3.ad.ibbr.umd.edu:8006/api2/json/cluster/resources?type=vm', cookies={'PVEAuthCookie': ticket})

try:
    fname = "vms-{}.json".format(datetime.datetime.now().strftime('%Y%m%d-%H%M'))
    fp = open(fname,mode='w')
except:
    print("Aiiee 3")

fp.write(json.dumps(json.loads(vms.text), sort_keys=True, indent=4 ))
fp.close()



#print(response)
#print(response.headers)
