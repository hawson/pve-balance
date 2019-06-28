# simple class for nodes.  Mostly a wrapper around
# data from proxmoxer

import logging
import functools

@functools.total_ordering
class Node:

    # Formatting string fro score output
    fmt = '{name:25} {cpu}/{maxcpu}(%{cpu_perc}) {maxmem}G(%{mem_perc}) score: {score}'

    shown = False

    weight = {
        'mem':  1.0,
        'disk': 0.0,   # This will be normalized to GB (not bytes
        'cpu':  1.0,   # CPU utilization as "fraction_as_percentage",
        'net':  1.0,   # This will be normalized to MB/sec (not Mbps)
        'ncpu': 1*8.0, # Scale up total CPU count, to account for oversubscription
    }


    def __init__(self, data=None, bias=0.0, minfreecpu=1, minfreemem_perc=0.10):
        if data:
            for k, v in data.items():
                setattr(self, k, v)
            self.name = data['node']

        self.log = logging.getLogger(__name__)

        self.bias = bias
        self.allocated_vms = []

        self.freecpu = self.maxcpu
        self.freemem = self.maxmem - self.mem

        self.minfreecpu = minfreecpu
        self.minfreemem = minfreemem_perc * self.maxmem


    def __str__(self):
        return self.name

    def __eq__(self, other):
        return(self.status, self.id) == (other.status, other.id)

    def __lt__(self, other):
        return(self.status, self.id)  < (other.status, other.id)


    def area_perc(self):
        return float(self.mem / 2**30) * self.cpu

    def area(self):
        return float(self.maxmem / 2**30) * self.maxcpu


    def dash(self,n, dash='-'):
        return dash*n


    def show(self):

        if not Node.shown:
            Node.shown = True
            print(Node.fmt.format(
                name=self.dash(25),
                cpu=self.dash(3),
                maxcpu=self.dash(2),
                cpu_perc=self.dash(2),
                maxmem=self.dash(3),
                mem_perc=self.dash(3),
                score=self.dash(15),
            ))

        print(Node.fmt.format(
            name     = self.id,
            cpu      = '{:>02.1f}'.format(self.cpu),
            maxcpu   = '{:>2}'.format(self.maxcpu),
            cpu_perc = '{:>2.0f}'.format(float( float(self.cpu)/float(self.maxcpu)*100)),
            maxmem   = '{:>3.0f}'.format(int(self.maxmem / 2**30)),
            mem_perc = '{:>2.0f}'.format(float( float(self.mem)/float(self.maxmem)*100)),
            score    = self.score(full=True)

            #cpu      = '{d}'.format(self.cpu),
            #maxcpu   = '{d}'.format(self.maxcpu),
            #maxmem   = '{>3d}'.format(self.maxmem / 2**30),
            #cpu_perc = '{>4.2f}'.format(float( float(self.cpu)/float(self.maxcpu )*100) ),
            #mem_perc = '{>4.2f}'.format(float( float(self.mem)/float(self.maxmem )*100) ),
            #score    = score_node(name,loadout, mode='total', output='full'),
        ))

        return


    def allocate(self, vm):
        if self.has_space(vm, quiet=True):
            self.freemem -= vm.maxmem
            self.freecpu -= vm.maxcpu
            self.allocated_vms.append(vm)
            return True
        return False



    def has_space(self, vm, quiet=False):
        '''Takes a vm, and returns True/False if there is space for it'''
        if not quiet:
            self.log.debug("    {} n{:>.1f} > v{:>.1f}  and n{} > v{}".format(self.name, self.freemem/2**30, vm.maxmem/2**30, self.freecpu, vm.maxcpu))
        if self.freemem - self.minfreemem > vm.maxmem:
            if self.freecpu - self.minfreecpu > vm.maxcpu:
                return True
        return False




    def score(self, full=False, mode='total', biased=True):
        score = 0.0

        node_score = 0.0
        vm_score   = 0.0

        scores = {
            'cpu': 0.0,
            'mem': 0.0,
            'net': 0.0,
            'disk': 0.0,
            'vm': 0.0,
            'bias': self.bias if biased else 0.0,
        }

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

