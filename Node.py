# simple class for nodes.  Mostly a wrapper around
# data from proxmoxer

import logging

class Node:

    # Formatting string fro score output
    fmt='{name:25} {cpu}/{maxcpu}(%{cpu_perc}) {maxmem}G(%{mem_perc}) score: {score}'

    weight = {
        'mem':  1.0,
        'disk': 0.0,   # This will be normalized to GB (not bytes
        'cpu':  1.0,   # CPU utilization as "fraction_as_percentage",
        'net':  1.0,   # This will be normalized to MB/sec (not Mbps)
        'ncpu': 1/8.0, # Scale down total CPU count, bias more towards usage
    }


    def __init__(self, data=None, bias=0.0):

        if data:
            for k,v in data.items():
                setattr(self, k, v)
            self.name=data['node']
        self.log = logging.getLogger(__name__)
        self.bias=bias


    def show(self, format=None):

        print(Node.fmt.format(
            name     = self.id,
            cpu      = '{:>02.1f}'.format(self.cpu),
            maxcpu   = '{:>2}'.format(self.maxcpu),
            cpu_perc = '{:>2.0f}'.format(float( float(self.cpu)/float(self.maxcpu )*100)),
            maxmem   = '{:>3.0f}'.format(int(self.maxmem / 2**30)),
            mem_perc = '{:>2.0f}'.format(float( float(self.mem)/float(self.maxmem )*100)),
            score    = self.score(full=True)

            #cpu      = '{d}'.format(self.cpu),
            #maxcpu   = '{d}'.format(self.maxcpu),
            #maxmem   = '{>3d}'.format(self.maxmem / 2**30),
            #cpu_perc = '{>4.2f}'.format(float( float(self.cpu)/float(self.maxcpu )*100) ),
            #mem_perc = '{>4.2f}'.format(float( float(self.mem)/float(self.maxmem )*100) ),
            #score    = score_node(name,loadout, mode='total', output='full'),
        ))



    def score(self, full=False, mode='total', biased=True, output='short'):
        score = 0.0

        node_score = 0.0
        vm_score   = 0.0

        scores = {
            'cpu': 0.0,
            'mem': 0.0,
            'net': 0.0,
            'disk': 0.0,
            'vm': 0.0,
            'bias': self.bias,
        }

        node_name = self.name

        if mode == 'total' or mode == 'node':
            # metrics we care about
            cpu    = self.cpu
            maxcpu = self.maxcpu
            maxmem = self.maxmem
            mem    = self.mem
            #net    = node['netin'] + node['netout']
            #disk   = node['diskread'] + node['diskwrite']

            scores['cpu'] = cpu/maxcpu * Node.weight['cpu']
            scores['mem'] = mem/maxmem * Node.weight['mem']

#         if mode == 'total' or mode == 'vm':
#            for vmid, vm in loadout.items():
#                if vm['node'] != node_name:
#                    continue
#
#                vm_score += score_vm(vm, biased)

        score = sum(scores.values())

        if full:
            return '{:6.3f} = {:5.3f} + {:5.3f} + {:3.1f}'.format(
                    score,
                    scores['cpu'],
                    scores['mem'],
                    scores['bias'],
                    )
        else:
            return '{:>.3f}'.format(score)

