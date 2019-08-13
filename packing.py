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
import random

log = logging.getLogger(__name__)

def pack_setup(orig_nodes, orig_vms, vm_sort_key='area', vm_reverse=True, vm_random=False):
    '''makes master lists of nodes and vms for packing'''

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

    if vm_random:
        random.shuffle(vms)
    else:
        vms.sort(key=lambda v: getattr(v, vm_sort_key)(), reverse=vm_reverse)

    logging.debug("Sorted VM order (by {}, rev:{}): {}".format(vm_sort_key, vm_reverse, list(map(str,vms))))


    return nodes, vms


def pack_size(orig_nodes, orig_vms, key='area', vm_reverse=True, vm_random=False):
    '''A naive packing routine that only allocates by "size" of
    a VM, filling a single node to capacity, then moving along
    to the next node.  Returns a list of *NEW* nodes with the new packing
    Valid sort keys=[ score, area, area_perc ]'''

    log.info("Packing by size")

    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key, vm_reverse=vm_reverse, vm_random=vm_random)

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


def pack_size_rr(orig_nodes, orig_vms, key='area', vm_reverse=True, vm_random=False):
    '''a slightly less naive packing routine that only allocates nodes,
    but rotates round-robin style over the nodes to attempt a more
    balanced allocation.'''

    log.info("Packing by size, RR")

    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key, vm_reverse=vm_reverse, vm_random=vm_random)
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
def pack_size_df(orig_nodes, orig_vms, key='area', vm_reverse=True, vm_random=False):
    '''Pack by dot product comparison'''

    import balance_math

    log.info("Packing by dot-product in closet.")

    # Basic sorting and setup
    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key, vm_reverse=vm_reverse, vm_random=vm_random)



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

            # vector for the VM, to be compared against the nodes
            vm_vect = balance_math.norm([ vm.maxmem_gb, vm.maxcpu])

            log.info("Attempt placing {}({:>.1f}GB,{} cpu) = {} [{:.3f}, {:.3f}]".format(vm, vm.maxmem/2**30, vm.maxcpu, vm.area(), *vm_vect))
            allocated = False


            node_delta = {}
            node_vect = {}

            for node in nodes:
                # compute normalized vectors describing the resource dimensions,
                # this will be used in comparisons later.
                node_vect[node.name] = balance_math.norm( [ node.freemem_gb - node.minfreemem_gb, node.freecpu - node.minfreecpu ])

                # Compute the difference between the VM vector and node vector.
                # This will be used to sort the node list
                node_delta[node.name] = balance_math.length(balance_math.diff(vm_vect,node_vect[node.name]))
                log.info("  Node delta={:.3f}".format(node_delta[node.name]))

            # Sort the nodes according to similarity to the VM being packed.
            nodes.sort(key=lambda n: node_delta[n.name])

            for node in nodes:
                log.info("  on {} [{:.3f},{:.3f}]:".format(node, *node_vect[node.name]))

                if node.allocate(vm):
                    log.info("  Placed {} on {}".format(vm, node))
                    allocations += 1
                    allocated_vms.append(vm)
                    allocated = True
                    break

            if not allocated:
                log.info("  Failed to place {}".format(vm))



        # remove any allocated VMs from the master list
        for vm in allocated_vms:
            if vm in vms:
                vms.remove(vm)

        # if nothing was allocated, we're done, and break out of the
        # outermost while loop
        if allocations == 0:
            break


    return nodes, len(allocated_vms), len(vms)


############################################################################3
# random packing
def pack_random(orig_nodes, orig_vms, key='area', vm_reverse=True, vm_random=False):
    '''Do it randomly, every time'''


    log.info("Random packing")

    # Basic sorting and setup
    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key, vm_reverse=vm_reverse, vm_random=vm_random)

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
        random.shuffle(vms)
        for vm in vms:
            log.info("Attempt placing {}({:>.1f}GB,{} cpu) = {}".format(vm, vm.maxmem/2**30, vm.maxcpu, vm.area()))
            # Magic here

            random.shuffle(nodes)
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


        # remove any allocated VMs from the master list
        for vm in allocated_vms:
            if vm in vms:
                vms.remove(vm)

        # if nothing was allocated, we're done, and break out of the
        # outermost while loop
        if allocations == 0:
            break

    return nodes, len(allocated_vms), len(vms)
############################################################################3
############################################################################3
# boilerplate for other packing methods
def pack_skeleton(orig_nodes, orig_vms, key='area', vm_reverse=True, vm_random=False):
    '''Skeleton text about the packing routine.'''

    log.info("Packing skeletons in closet.")

    # Basic sorting and setup
    nodes, vms = pack_setup(orig_nodes, orig_vms, vm_sort_key=key, vm_reverse=vm_reverse, vm_random=vm_random)

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

        # remove any allocated VMs from the master list
        for vm in allocated_vms:
            if vm in vms:
                vms.remove(vm)

        # if nothing was allocated, we're done, and break out of the
        # outermost while loop
        if allocations == 0:
            break

    return nodes, len(allocated_vms), len(vms)
