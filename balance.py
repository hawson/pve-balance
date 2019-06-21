#!/usr/bin/env python3

import os
import re
import sys
import json


from proxmoxer import ProxmoxAPI
proxmox = ProxmoxAPI('pve3.ad.ibbr.umd.edu', user='monitoring@pve', password='monitoring',)


nodes = {}
vms = {}

weight = {
    'mem':  1.0,
    'disk': 0.0,   # This will be normalized to GB (not bytes
    'cpu':  1.0,   # CPU utilization as "fraction_as_percentage",
    'net':  1.0,   # This will be normalized to MB/sec (not Mbps)
    'ncpu': 1/4.0, # Scale down total CPU count, bias more towards usage
}

# these values are added directly to the compute score of each VM/Node
global_bias = {
    'pve1': 10,
    'bcmd7': -10,
}


#
# https://pve.proxmox.com/pve-docs/api-viewer/index.html
#

def get_stats_node(proxmox, exclude=[]):
    nodes = {}
    for node in proxmox.nodes.get():
        if node['node'] not in exclude:
            nodes[node['node']] = node
        else:
            print("excluding {}".format(node['node']))
        

    return nodes

def show_nodes(nodes, loadout, format='std'):
    # 'pve1': {'ssl_fingerprint': 'C5:48:BB:72:74:20:3A:C5:11:54:5A:D2:99:88:E5:C6:68:50:28:43:A6:E5:B7:C4:E7:26:BC:F3:A5:72:38:EF', 'disk': 5917954048, 'id': 'node/pve1', 'node': 'pve1', 'type': 'node', 'mem': 46294081536, 'maxcpu': 40, 'uptime': 1953914, 'maxmem': 134842212352, 'status': 'online', 'cpu': 0.00900691538434386, 'level': '', 'maxdisk': 16578916352}
    #print(nodes)

    fmt='{name:5>} {cpu:>2}/{maxcpu:>2}(%{cpu_perc:>2.0f}) {maxmem:>5s}(%{mem_perc:>2.0f}) score: {score:>8}'

    for name,node in sorted(nodes.items()):
        print(fmt.format(
            name     = name,
            cpu      = human_format(node['cpu'], precision=0),
            maxcpu   = human_format(node['maxcpu'], precision=0),
            maxmem   = human_format(node['maxmem'], precision=0),
            cpu_perc = float( human_format( float(node['cpu'])/float(node['maxcpu'] )*100) ),
            mem_perc = float( human_format( float(node['mem'])/float(node['maxmem'] )*100) ),
            score    = score_node(node,loadout, mode='total', output='full'),
        ))



def get_stats_vm(proxmox, exclude=[]):

    vms = {}
    for vm in proxmox.cluster.resources.get(type='vm'):
        #print(vm)
        if vm['name'] not in exclude and vm['vmid'] not in exclude:
            vms[vm['vmid']] = vm
        else:
            print("excluding {}/{}".format(vm['vmid'],vm['name']))
        
    #for vm in vms:
    #    print("{0} {1} => {2}".format(vm, vms[vm]['name'], human_format(vms[vm]['maxmem'])))

    return vms


def show_vms(vms, mode='std'):
    # 13: {'maxdisk': 34359738368, 'cpu': 0.00789133085414431, 'template': 0, 'netout': 11398084099, 'node': 'pve1', 'id': 'qemu/113', 'pool': 'ibbr', 'netin': 6947826280, 'diskwrite': 65830185472, 'maxmem': 2097152000, 'status': 'running', 'diskread': 64368749240, 'name': 'cephtest3', 'uptime': 918537, 'maxcpu': 2, 'mem': 733351936, 'type': 'qemu', 'disk': 0, 'vmid': 113}
    #print(vms)
    fmt='{vmid:5>} {name:>20} {cpu:>2}/{maxcpu:>2}(%{cpu_perc:>2.0f}) {maxmem:>3} {node}'
    for vmid,vm in sorted(vms.items()):
        #print("{0} {1} => {2}".format(node, nodes[node]['uptime'], nodes[node]['disk']))
        print(fmt.format(
            name = vm['name'],
            vmid=vmid,
            cpu    = human_format(vm['cpu'],precision=0),
            maxcpu = human_format(vm['maxcpu'],precision=0),
            maxmem = human_format(vm['maxmem']),
            node = vm['node'],
            cpu_perc = float( human_format( float(vm['cpu'])/float(vm['maxcpu'] )*100) )
        ))


def human_format(num,precision=1):
    magnitude = 0
    while abs(num) >= 1024:
        magnitude += 1
        num /= 1024.0
    # add more suffixes if you need them
    format_str = '%.' + str(precision) + 'f%s'
    #return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
    return format_str % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


def score_vm(vm, biased):
    bias_score = 0.0
    name = vm['name']
    if biased:
        if name in global_bias:
            bias_score = global_bias[vm['name']]

    return (vm['cpu']                  * weight['cpu']   # percentage of allocated CPU used
            +vm['maxcpu']              * weight['ncpu']  # number of CPUs
            +vm['mem']/vm['maxmem']    * weight['mem']   # Calculate % RAM used
            +vm['maxdisk']             * weight['disk'] / 1073741824
            #+(vm['netin']+vm['netout']) * weight['net'] / 1048576 +
            + bias_score
           )

def score_node(node, loadout, mode='total', biased=True, output='short'):
    '''How we generate a "score" for a node, given a specific loadout of VMs'''
    score = 0.0

    node_score = 0.0
    vm_score   = 0.0
    node_bias  = 0.0
    vm_bias    = 0.0
    
    node_name = node['node']

    if mode == 'total' or mode == 'node':
        # metrics we care about
        cpu    = node['cpu']
        maxcpu = node['maxcpu']
        maxmem = node['maxmem']
        mem    = node['mem']
        #net    = node['netin'] + node['netout']
        #disk   = node['diskread'] + node['diskwrite']


        node_score = (cpu/maxcpu * weight['cpu'] +
                      mem/maxmem * weight['mem'])

    if mode == 'total' or mode == 'vm':
        for vmid, vm in loadout.items():
            if vm['node'] != node_name:
                continue

            vm_score += score_vm(vm, biased)


    # calculate bias
    if biased:
        if node_name in global_bias:
            node_bias = global_bias[node_name]

    score = node_score + vm_score + node_bias + vm_bias
    if output=='full':
        return '{:6.3f} = {:5.3f} + {:5.3f} + {:4.1f} + {:4.1f}'.format(score, node_score, vm_score, node_bias, vm_bias)
    return human_format(score,precision=3)




nodes = get_stats_node(proxmox, exclude='badnode')
vms   = get_stats_vm(proxmox, exclude=['cephtest2'])

show_nodes(nodes, vms)
show_vms(vms)


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
