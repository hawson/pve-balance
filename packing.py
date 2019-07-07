'''Given a list of Hypervisors, and a loadout of VMs
pack them most efficiently.
Note that optimal packing assumes zero cost for
transitions. :)'''


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
from balance_math import *

log = logging.getLogger(__name__)

def pack_size(orig_nodes, orig_vms, key='area'):
    '''A naive packing routine that only allocates by "size" of
    a VM, filling a single node to capacity, then moving along
    to the next node.  Returns a list of *NEW* nodes with the new packing
    Valid sort keys=[ score, area, area_perc ]'''

    log.info("Packing by size")

    vm_metrics = {}

    # sort by the total "area"
    vms = orig_vms.copy()

    nodes = sorted(orig_nodes.copy(), key=lambda n: n.area(), reverse=True)

    for node in nodes:
        node.allocated_vms = []


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


    #List is already sorted, so fill up as much as possible.
    allocated_vms = []
    while vms:

        allocations = 0


        for vm in vms:
            #print(list(map(str,vms)))
            #print(list(map(str,allocated_vms)))
            log.info("Attempt placing {}({:>.1f}GB,{} cpu) = {}".format(vm, vm.maxmem/2**30, vm.maxcpu, vm.area()))
            allocated = False
            for node in nodes:
                log.info("  on {}:".format(node))

                if node.allocate(vm):
                    log.info("  Placed {} on {}".format(vm, node))
                    allocations += 1
                    allocated_vms.append(vm)
                    allocated = True
                    break

            if not allocated:
                log.info("  Failed to place {}".format(vm))

        for vm in allocated_vms:
            if vm in vms:
                vms.remove(vm)

        # if nothing was allocated, we're done, and break out of the
        # outermost while loop
        if allocations == 0:
            break

    if vms:
        log.error("Failed to place {}  VMs! {}".format(len(vms), list(map(str, vms))))
    else:
        log.info("Successfully packed all {} VMs".format(len(orig_vms)))


    # Print vms by node
    for node in sorted(nodes):
        print(node.name)
        for vm in sorted(node.allocated_vms):
            print('  {}'.format(vm))


    return nodes, len(allocated_vms), len(vms)


# a slightly less naive packing routine that only allocates "size",
# looping over all nodes at once, so long as there is capacity in
# any node.
def pack_size_rr(orig_nodes, vms):
    log.info("Packing by size, RR")
    nodes = orig_nodes.copy()
    allocated_vms = vms.copy()

    return nodes, len(allocated_vms), len(vms)

# Try to allocate VMs to nodes based on similarities of node
# to hypervisors, based on dot-products of the (normalized)
# dimensions of the nodes and VMs.
def pack_size_df(orig_nodes,vms):
    log.info("Packing by DF")
    nodes = orig_nodes.copy()
    allocated_vms = vms.copy()


    return nodes, len(allocated_vms), len(vms)
