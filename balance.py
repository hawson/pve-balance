#!/usr/bin/env python3

import os
import re
import sys
import json
import copy

import logging
import argparse

from PVE import PVE

import packing
import graphics



H = 'pve3.ad.ibbr.umd.edu'
U = 'monitoring@pve'
P = 'monitoring'

nodes = {}
vms = {}

#
# https://pve.proxmox.com/pve-docs/api-viewer/index.html
#


#####################
# Argument parsing

parser = argparse.ArgumentParser(
    description='''
Exactly two arguments may be passed on the CLI.  The first
must be a JSON dump of the node definitions; the second must
be a JSON dump of the VM definitions.
''')

parser.add_argument('-c', '--current', action='store_true', help="Only show current status.")
parser.add_argument('-n', '--nopics',  action='store_true', help="Do not generate output picutres", default=False)
parser.add_argument('-a', '--allocated',action='store_true', help="Show allocated CPU/RAM, in addition to max usage", default=False)
parser.add_argument('-v', '--verbose', action='count',      help="Be verbose, (multiples okay)")

parser.add_argument('-H', '--host',
    action='store',
    help="Hostname to connect to proxmox API endpoint",
    default='pve3.ad.ibbr.umd.edu')

# Default Username
parser.add_argument('-u', '--username',
    action='store',
    help="Proxmox API username",
    default="monitoring@pve")

# Default Password
parser.add_argument('-p', '--password',
    action='store',
    help="Proxmox API password (hint: store password in ENV variable, and pass that on CLI)",
    default="monitoring")


parser.add_argument('json_files', nargs='*', action='store')

try:
    parsed_options, remaining_args = parser.parse_known_args()

except SystemExit as exc:
    print('''
Error parsing arguments.
'''.format( ) )
    sys.exit(1)


verbose_value = 0 if parsed_options.verbose is None else parsed_options.verbose
LOG_LEVEL = max(1, 30 - verbose_value * 10)
logging.basicConfig(format='%(asctime)-15s [%(levelname)s] %(message)s', level=LOG_LEVEL)

logging.debug(parsed_options)
logging.debug(remaining_args)


if parsed_options.json_files:

    logging.debug(parsed_options.json_files)

    if len(parsed_options.json_files) == 2:

        import Node
        import VM

        fp = open(parsed_options.json_files[0])
        node_list = json.load(fp)
        fp.close()

        fp = open(parsed_options.json_files[1])
        vm_list = json.load(fp)
        fp.close()

        logging.debug("Parsed node JSON=%s",str(node_list))
        #logging.debug("Parsed VM JSON=%s",+str(vm_list))

        # Build Node and VM objects from imported JSON data
        nodes = [ Node.Node(data=n) for n in node_list['data'] ]
        vms = [ VM.VM(data=v) for v in vm_list['data'] ]

    else:
        parser.print_help()
        sys.exit(1)

else:
    #proxmox = ProxmoxAPI(H, password=P, user=U)
    #P = PVE(host=H, u=U, pw=P, excludes=['pve3'])
    P = PVE(host=parsed_options.host, u=parsed_options.username, pw=parsed_options.password, excludes=['badnode'])

    print("Dumping Nodes")
    nodes = P.get_nodes(full=True)

    print("Dumping VMs")

    #vms = P.get_vms(full=False, filter_node='pve2')
    vms = P.get_vms(full=True, )



#print(vms)
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


temp_nodes = copy.deepcopy(nodes)
temp_vms = copy.deepcopy(vms)
temp_vms.sort(key=lambda x: x.area())

for tvm in temp_vms:
    print('{:>25}: {:>.4f} {:>.4f}'.format(tvm.name, tvm.area_perc(), tvm.area()))


print("Current status....")


packed_nodes, packed_count, unpacked_count = packing.pack_null(temp_nodes, temp_vms, key='area')

if not parsed_options.nopics:
    g=graphics.graphics(packed_nodes, height=600, width=800, filename="current", show_allocated=parsed_options.allocated)
    g.save()


if parsed_options.current:
    sys.exit(0)




print("Packing....")



packed_nodes, packed_count, unpacked_count = packing.pack_size(temp_nodes, temp_vms, key='area')

if not parsed_options.nopics:
    g=graphics.graphics(packed_nodes, height=600, width=800, filename="packed", show_allocated=parsed_options.allocated)
    g.save()


print("Packed {}/{} nodes. ({:.0f}%)".format(packed_count, unpacked_count+packed_count, 100*packed_count/(packed_count+unpacked_count)))

for node in packed_nodes:
    node.efficency()

#========================================================================
#temp_nodes = copy.deepcopy(nodes)
temp_vms = copy.deepcopy(vms)
packed_nodes, packed_count, unpacked_count = packing.pack_size_rr(temp_nodes, temp_vms, key='area')

if not parsed_options.nopics:
    g=graphics.graphics(packed_nodes, height=600, width=800, filename="packed_rr", show_allocated=parsed_options.allocated)
    g.save()


print("Packed {}/{} nodes. ({:.0f}%)".format(packed_count, unpacked_count+packed_count, 100*packed_count/(packed_count+unpacked_count)))


for node in packed_nodes:
    node.efficency()


#========================================================================
#temp_nodes = copy.deepcopy(nodes)
temp_vms = copy.deepcopy(vms)
packed_nodes, packed_count, unpacked_count = packing.pack_size_df(temp_nodes, temp_vms, key='area')

if not parsed_options.nopics:
    g=graphics.graphics(packed_nodes, height=600, width=800, filename="packed_df", show_allocated=parsed_options.allocated)
    g.save()


print("Packed {}/{} nodes. ({:.0f}%)".format(packed_count, unpacked_count+packed_count, 100*packed_count/(packed_count+unpacked_count)))


for node in packed_nodes:
    node.efficency()


#========================================================================
#temp_nodes = copy.deepcopy(nodes)
temp_vms = copy.deepcopy(vms)
packed_nodes, packed_count, unpacked_count = packing.pack_random(temp_nodes, temp_vms, key='area')

if not parsed_options.nopics:
    g=graphics.graphics(packed_nodes, height=600, width=800, filename="packed_random", show_allocated=parsed_options.allocated)
    g.save()


print("Packed {}/{} nodes. ({:.0f}%)".format(packed_count, unpacked_count+packed_count, 100*packed_count/(packed_count+unpacked_count)))


for node in packed_nodes:
    node.efficency()



#######################################################################

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
