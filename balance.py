#!/usr/bin/env python3

import os
import re
import sys
import json

import logging

from PVE import PVE

import packing
import graphics



LOG_LEVEL = 1

logging.basicConfig(format='%(asctime)-15s [%(levelname)s] %(message)s', level=LOG_LEVEL)


H = 'pve3.ad.ibbr.umd.edu'
U = 'monitoring@pve'
P = 'monitoring'

nodes = {}
vms = {}

#
# https://pve.proxmox.com/pve-docs/api-viewer/index.html
#

def human_format(num, precision=1):
    magnitude = 0
    while abs(num) >= 1024:
        magnitude += 1
        num /= 1024.0
    # add more suffixes if you need them
    format_str = '%.' + str(precision) + 'f%s'
    #return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
    return format_str % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])



if len(sys.argv)>1:
    import Node
    import VM

    fp = open(sys.argv[1])
    node_list = json.load(fp)
    fp.close()

    fp = open(sys.argv[2])
    vm_list = json.load(fp)
    fp.close()

    print(node_list)

    nodes = [ Node.Node(data=n) for n in node_list['data'] ]
    vms = [ VM.VM(data=v) for v in vm_list['data'] ]

    print(nodes)
    print(vms)

else:
    #proxmox = ProxmoxAPI(H, password=P, user=U)
    #P = PVE(host=H, u=U, pw=P, excludes=['pve3'])
    P = PVE(host=H, u=U, pw=P, excludes=['badnode'])

    print("Dumping Nodes")
    nodes = P.get_nodes(full=True)

    print("Dumping VMs")

    #vms = P.get_vms(full=False, filter_node='pve2')
    vms = P.get_vms(full=True, )


print(vms)

#print(nodes)
[x.show() for x in nodes]
[x.show() for x in vms  ]

temp_vms = vms.copy()

#for tvm in sorted(temp_vms):
#    log.info('{}: {}'.format(tvm.node, tvm.name))


# Print vms by node
for node in sorted(nodes):
    print(node.name)
    for tvm in sorted(temp_vms):
        if tvm.node == node.name:
            temp_vms.remove(tvm)
            print('  {}'.format(tvm.name))


temp_vms = vms.copy()
temp_vms.sort(key=lambda x: x.area_perc())

for tvm in temp_vms:
    print('{:>25}: {}'.format(tvm.name, tvm.area_perc()))



print("Packing....")


pack = {}
pack = packing.pack_size(nodes, vms)
#packing.pack_size_rr(nodes, vms)
#packing.pack_size_df(nodes, vms)

g=graphics.graphics('output', pack, nodes, vms, height=600, width=800)
g.save()


#print(P.get_nodes())
#print(P.get_vms())


# 'pve1': {
#    'cpu': 0.00900691538434386,
#    'disk': 5917954048,
#    'id': 'node/pve1',
#    'level': '',
#    'maxcpu': 40,
#    'maxdisk': 16578916352
#    'maxmem': 134842212352,
#    'mem': 46294081536,
#    'node': 'pve1',
#    'ssl_fingerprint': 'C5:50:28:43:A6:E5:B7:C4:E7:26:BC:F3:A5:72:38:EF',
#    'status': 'online',
#    'type': 'node',
#    'uptime': 1953914,
#}

# 113: {
#    'cpu': 0.00789133085414431,
#    'disk': 0,
#    'diskread': 64368749240,
#    'diskwrite': 65830185472,
#    'id': 'qemu/113',
#    'maxcpu': 2,
#    'maxdisk': 34359738368,
#    'maxmem': 2097152000,
#    'mem': 733351936,
#    'name': 'cephtest3',
#    'netin': 6947826280,
#    'netout': 11398084099,
#    'node': 'pve1',
#    'pool': 'ibbr',
#    'status': 'running',
#    'template': 0,
#    'type': 'qemu',
#    'uptime': 918537,
#    'vmid': 113
#}
