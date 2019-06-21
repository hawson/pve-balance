#!/usr/bin/env python3

import os
import re
import sys


from proxmoxer import ProxmoxAPI
proxmox = ProxmoxAPI('pve3.ad.ibbr.umd.edu', user='monitoring@pve', password='heres looking at you kid',)


nodes = {}
vms = {}

weight = {
    'mem': 1.0,
    'disk': 0.0,
    'cpu': 1.0,
    'net': 1.0,
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
        
    for node in nodes:
        print("{0} {1} => {2}".format(node, nodes[node]['uptime'], nodes[node]['disk']))

    return nodes



def get_stats_vm(proxmox, exclude=[]):

    vms = {}
    for vm in proxmox.cluster.resources.get(type='vm'):
        #print(vm)
        if vm['name'] not in exclude and vm['vmid'] not in exclude:
            vms[vm['vmid']] = vm
        else:
            print("excluding {}/{}".format(vm['vmid'],vm['name']))
        
    for vm in vms:
        print("{0} {1} => {2}".format(vm, vms[vm]['name'], human_format(vms[vm]['maxmem'])))

    return vms


def human_format(num,precision=1):
    magnitude = 0
    while abs(num) >= 1024:
        magnitude += 1
        num /= 1024.0
    # add more suffixes if you need them
    format_str = '%.' + str(precision) + 'f%s'
    #return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
    return format_str % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

nodes = get_stats_node(proxmox, exclude='pve3')
vms   = get_stats_vm(proxmox, exclude=['cephtest2'])



