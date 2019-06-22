# Score computation

weight = {
    'mem':  1.0,
    'disk': 0.0,   # This will be normalized to GB (not bytes
    'cpu':  1.0,   # CPU utilization as "fraction_as_percentage",
    'net':  1.0,   # This will be normalized to MB/sec (not Mbps)
    'ncpu': 1/8.0, # Scale down total CPU count, bias more towards usage
}


# these values are added directly to the compute score of each VM/Node
global_bias = {
    'pve1': 10,
    'bcmd7': -10,
}




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




