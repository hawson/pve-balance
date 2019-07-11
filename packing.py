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
import copy

log = logging.getLogger(__name__)

def pack_setup(orig_nodes, orig_vms, vm_sort_key='area'):

    nodes = copy.deepcopy(orig_nodes)
    nodes.sort(key=lambda n: n.area(), reverse=True)
    logging.debug("Sorted node order (by area): {}".format(list(map(str,nodes))))

    for node in nodes:
        node.allocated_vms = []

    try:
        getattr(orig_vms[0], vm_sort_key)
    except AttributeError:
        raise NotImplementedError("The vm class does not have {} a method".format(vm_sort_key))

    log.info("Found method {}".format(vm_sort_key))

    vms = orig_vms.copy()
    vms.sort(key=lambda v: getattr(v, vm_sort_key)(), reverse=True)

    logging.debug("Sorted VM order (by {}): {}".format(vm_sort_key, list(map(str,vms))))


    return nodes, vms


def pack_size(orig_nodes, orig_vms, key='area'):
    '''A naive packing routine that only allocates by "size" of
    a VM, filling a single node to capacity, then moving along
    to the next node.  Returns a list of *NEW* nodes with the new packing
    Valid sort keys=[ score, area, area_perc ]'''

    log.info("Packing by size")

    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key)

#    vm_metrics = {}
#
#    for vm in vms:
#        metrics = {}
#
#        # scale RAM to GB
#        metrics['area'] = vm.area()
#        metrics['area_perc'] = vm.area_perc()
#        metrics['score'] = vm.score()
#
#        vm_metrics[vm.vmid] = metrics


    allocated_vms = []

    #List is already sorted, so fill up as much as possible.
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


def pack_size_rr(orig_nodes, orig_vms, key='area'):
    '''a slightly less naive packing routine that only allocates nodes,
    but rotates round-robin style over the nodes to attempt a more
    balanced allocation.'''

    log.info("Packing by size, RR")

    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key)
    allocated_vms = []

    while vms:

        allocations = 0
        node_index = 0
        nodes_avail = len(nodes)

        for vm in vms:
            log.info("Attempt placing {}({:>.1f}GB,{} cpu) = {}".format(vm, vm.maxmem/2**30, vm.maxcpu, vm.area()))
            allocated = False

            for i in range(nodes_avail):    # pylint: disable=unused-variable

                node_index += 1
                node = nodes[node_index % nodes_avail]

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




# Try to allocate VMs to nodes based on similarities of node
# to hypervisors, based on dot-products of the (normalized)
# dimensions of the nodes and VMs.
def pack_size_df(orig_nodes, orig_vms, key='area'):
    '''Pack by dot product comparison'''

    log.info("Packing by dot-product in closet.")

    # Basic sorting and setup
    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key)

    # initially empty list of VMs that have been placed somewhere.
    # if it isn't in this list, it wasn't placed.
    allocated_vms = []

    # Loop so long as there are vms to process
    while vms:

        # If allocations is zero at the end of this pass,
        # we've done nothing, and break out.
        allocations = 0

        # Sequentially loop over all VMs in the list.  This list
        # was sorted in pack_setup() above, so no need to do it again.
        for vm in vms:
            log.info("Attempt placing {}({:>.1f}GB,{} cpu) = {}".format(vm, vm.maxmem/2**30, vm.maxcpu, vm.area()))
            # Magic here

            for node in nodes:
                log.info("  on {}:".format(node))
                # Magic here

    return nodes, len(allocated_vms), len(vms)


def pack_skeleton(orig_nodes, orig_vms, key='area'):
    '''Skeleton text about the packing routine.'''

    log.info("Packing skeletons in closet.")

    # Basic sorting and setup
    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key)

    # initially empty list of VMs that have been placed somewhere.
    # if it isn't in this list, it wasn't placed.
    allocated_vms = []

    # Loop so long as there are vms to process
    while vms:

        # If allocations is zero at the end of this pass,
        # we've done nothing, and break out.
        allocations = 0

        # Sequentially loop over all VMs in the list.  This list
        # was sorted in pack_setup() above, so no need to do it again.
        for vm in vms:
            log.info("Attempt placing {}({:>.1f}GB,{} cpu) = {}".format(vm, vm.maxmem/2**30, vm.maxcpu, vm.area()))
            # Magic here

            for node in nodes:
                log.info("  on {}:".format(node))
                # Magic here

            pass

        # if nothing was allocated, we're done, and break out of the
        # outermost while loop
        if allocations == 0:
            break

    return nodes, len(allocated_vms), len(vms)
