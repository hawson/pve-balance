# Given a list of Hypervisors, and a loadout of VMs
# pack them most efficiently.
# Note that optimal packing assumes zero cost for
# transitions. :)
#
#
# Packing is done via a dot-product method, initially
# using CPU and RAM.  The idea is to sort, placing the
# larger VMs first, adding them to the hypervisor (or "bin")
# that is most similar in proportions to themselves.  The
# idea being that the this is a more effiecent use of space.
#


#  +----------------------------------------+
#  | hypervisor-1                   VM-C+--+|
#  |                                    +--+|
#  |            +----------------------+    |
#  |            |VM-B       __________/|    |
#  |            | _________/  B        |    |
# R|            |/                     |    |
# A|            +----------------------+    |
# M|+----------+                            |
#  ||VM-A     /|                            |
#  ||     ___/ |                            |
#  || ___/ A   |                            |
#  ||/         |                            |
#  |+----------+                            |
#  +----------------------------------------+
#                 CPU
#
#  +-------------------------------+
#  | Hypervisor-2                  |
# R|+--------------+               |
# A||              |      <waste>  |
# M||              |               |
#  |+--------------+               |
#  +-------------------------------+
#                 CPU

# The trick here is to *remove* the consumed resources from the next
# iteration of placement.

import logging
log = logging.getLogger(__name__)

from balance_math import *


# a naive packing routine that only allocates by "size" of
# a VM, filling a single node to capacity, then moving along
# to the next node.
#
# Valid sort keys=[ score, area, area_perc ]
def pack_size(orig_nodes, orig_vms, key='area'):
    log.info("Packing by size")

    vm_metrics = {}

    # sort by the total "area"
    nodes = sorted(orig_nodes.copy(), key=lambda n: n.area(), reverse=True)

    for node in nodes:
        node.allocated_vms = []

    vms = orig_vms.copy()

    if   key == 'score':
        log.info("Sorting by score.")
        vms.sort(key=lambda v: v.score(), reverse=True)

    elif key == 'area':
        log.info("Sorting by area.")
        vms.sort(key=lambda v: v.area(), reverse=True)

    elif key == 'area_perc':
        log.info("Sorting by area_perc.")
        vms.sort(key=lambda v: v.area_perc(), reverse=True)



    for vm in vms:
        metrics = {}

        # scale RAM to GB
        metrics['area'] = vm.area()
        metrics['area_perc'] = vm.area_perc()
        metrics['score'] = vm.score()

        vm_metrics[vm.vmid] = metrics

    print(list(map(str,vms)))

    #List is already sorted, so fill up as much as possible.
    while vms:

        allocations = 0

        for vm in vms:
            log.info("Attempt placing {}({:>3.3f})".format(vm, vm.area()))
            for node in nodes:
                log.info("  on {}({:>3.3f}):".format(node, node.area()))
                if node.has_space(vm):
                    log.info("  Placed {} on {}".format(vm, node))
                    node.allocate(vm)
                    allocations += 1
                    vms.remove(vm)
                    break

        if allocations == 0:
            break

    if vms:
        log.error("Failed to place several VM! {}".format(list(map(str, vms))))
    else:
        log.info("Successfully packed all VMs")


    # Print vms by node
    for node in sorted(nodes):
        print(node.name)
        for vm in sorted(node.allocated_vms):
            print('  {}'.format(vm))


    return nodes


# a slightly less naive packing routine that only allocates "size",
# looping over all nodes at once, so long as there is capacity in
# any node.
def pack_size_rr(nodes, vms):
    log.info("Packing by size, RR")
    return

# Try to allocate VMs to nodes based on similarities of node
# to hypervisors, based on dot-products of the (normalized)
# dimensions of the nodes and VMs.
def pack_size_df(nodes,vms):
    log.info("Packing by DF")
    return
