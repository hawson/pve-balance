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

# a naive packing routine that only allocates by "size" of
# a VM, filling a single node to capacity, then moving along 
# to the next node.

import logging
log = logging.getLogger(__name__)

def pack_size(nodes, vms):
    log.info("Packing by size")
    return


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

