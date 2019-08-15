# simple class for nodes.  Mostly a wrapper around
# data from proxmoxer
'''The Node class represents a Proxmox hypervisor, and includes
broad specifications of resources (mostly CPU, RAM and disk), and current
utilization of those resources (CPU, RAM, disk, and network).'''

import logging
import functools


# include this so nodes can be "sorted" as objects
@functools.total_ordering
class Node:
    '''Main node class.'''

    # Formatting string fro score output
    fmt = '{name:25} {cpu}/{maxcpu}(%{cpu_perc}) {maxmem}G(%{mem_perc})     score: {score}'

    shown = False

    weight = {
        'mem':  1.0,
        'disk': 0.0,   # This will be normalized to GB (not bytes
        'cpu':  1.0,   # CPU utilization as "fraction_as_percentage",
        'net':  1.0,   # This will be normalized to MB/sec (not Mbps)
        'ncpu': 1*8.0, # Scale up total CPU count, to account for oversubscription
    }


    def __init__(self, data=None, bias=0.0, minfreecpu=1, minfreemem_perc=0.10):
        '''Intialize based on the JSON blob handed to us, plus several
        additional values either passed in (min free specs, bias), or computed.'''
        if data:
            for key, value in data.items():
                setattr(self, key, value)
            self.name = data['node']

        self.log = logging.getLogger(__name__)

        self.allocated_vms = []
        self.bias = bias

        self.freecpu = self.maxcpu
        self.freemem = self.maxmem

        self.maxmem_gb = self.maxmem/2**30

        if self.status == 'online':
            self.mem_gb = self.mem/2**30
            self.freemem_gb = self.freemem/2**30

            self.minfreecpu = minfreecpu
            self.minfreemem = minfreemem_perc * self.maxmem
            self.minfreemem_gb = self.minfreemem/2**30
        else:
            self.mem_gb = 0
            self.freemem_gb = 0

            self.minfreecpu = 0
            self.minfreemem = 0
            self.minfreemem_gb = 0

            self.cpu = 0
            self.mem = 0



    def __str__(self):
        return self.name

    def __eq__(self, other):
        return(self.status, self.id) == (other.status, other.id)

    def __lt__(self, other):
        return(self.status, self.id) < (other.status, other.id)


    def area_perc(self, minfree=False):
        '''returns the "area" based on the utilization numbers, not the potentially available resources'''
        if minfree:
            return float(self.mem_gb - self.minfreemem/2**30) * (self.cpu - self.minfreecpu)
        return float(self.mem_gb) * self.cpu

    def area(self, minfree=False):
        '''returns the "area" based on the potentially available resources'''
        if minfree:
            return float(self.maxmem_gb - self.minfreemem/2**30) * (self.maxcpu - self.minfreecpu)
        return float(self.maxmem_gb) * self.maxcpu


    def dash(self, num_dashes, dash='-'):
        '''return a bunch of dashes'''
        return dash*num_dashes


    def show(self):
        '''Pretty print a node, for use in tables and reports and such'''

        if not Node.shown:
            Node.shown = True
            print(Node.fmt.format(
                name=self.dash(25),
                cpu=self.dash(3),
                maxcpu=self.dash(2),
                cpu_perc=self.dash(2),
                maxmem=self.dash(3),
                mem_perc=self.dash(2),
                score=self.dash(15),
            ))

        print(Node.fmt.format(
            name     = self.id,
            cpu      = '{:>02.1f}'.format(self.cpu),
            maxcpu   = '{:>2}'.format(self.maxcpu),
            cpu_perc = '{:>2.0f}'.format(float( float(self.cpu)/float(self.maxcpu)*100)),
            maxmem   = '{:>3.0f}'.format(int(self.maxmem_gb)),
            mem_perc = '{:>2.0f}'.format(float( float(self.mem)/float(self.maxmem)*100)),
            score    = self.score(full=True)

            #cpu      = '{d}'.format(self.cpu),
            #maxcpu   = '{d}'.format(self.maxcpu),
            #maxmem   = '{>3d}'.format(self.maxmem / 2**30),
            #cpu_perc = '{>4.2f}'.format(float( float(self.cpu)/float(self.maxcpu )*100) ),
            #mem_perc = '{>4.2f}'.format(float( float(self.mem)/float(self.maxmem )*100) ),
            #score    = score_node(name,loadout, mode='total', output='full'),
        ))


    def allocate(self, vm, force=False):
        '''Allocate a VM to a node, if there is space.  "Free" resources
        are deducted accordingly.  True is returned if the node was
        allocated; False is returned otherwise.  If a vm is allocated,
        the self.allocated_vms list is updated accordingly with a copy
        of the VMa.'''

        if force or self.has_space(vm, quiet=False):
            self.freemem -= vm.maxmem
            self.freemem_gb = self.freemem/2**30
            self.freecpu -= vm.maxcpu
            self.allocated_vms.append(vm)
            if force:
                self.log.debug("  %s placement on %s forced.", vm.name, self.name)
            return True
        return False



    def has_space(self, vm, quiet=False):
        '''Takes a vm, and returns True/False if there is space for it'''
        if not quiet:
            mem_delta = self.freemem/2**30 - self.minfreemem/2**30
            cpu_delta = self.freecpu - self.minfreecpu
            self.log.debug("    {} (M{:>.1f}-m{:>.1f}=F{:>.1f}) > v{:>.1f}  and (n{}-{}={}) > v{}".format(
                self.name,
                self.freemem/2**30, self.minfreemem/2**30, mem_delta, vm.maxmem_gb,
                self.freecpu, self.minfreecpu, cpu_delta, vm.maxcpu))
        if self.freemem - self.minfreemem > vm.maxmem:
            if self.freecpu - self.minfreecpu > vm.maxcpu:
                return True
        return False


    def score(self, full=False, mode='total', biased=True):
        '''"Score" the node, based on various resource usage, weighting,
        and bias.  Generally speaking, the score is the weighted %actual
        usage plus a bias for the node (if any)'''

        score = 0.0

        scores = {
            'cpu': 0.0,
            'mem': 0.0,
            'net': 0.0,
            'disk': 0.0,
            'vm': 0.0,
            'bias': self.bias if biased else 0.0,
        }

        if mode in [ 'total', 'node']:
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
            return '{: 6.3f} = {: 5.3f} + {: 5.3f} + {:3.1f}'.format(
                score,
                scores['cpu'],
                scores['mem'],
                scores['bias'],
            )
        return '{:>.3f}'.format(score)


    def efficency(self, free=False, report=True):

        import balance_math

        # vector describing an empty node
        node_max_vector = [ self.maxmem_gb, self.maxcpu ]
        len_hv = balance_math.length(node_max_vector)

        # vector describing an empty node, accounting for reserved resources
        node_free_vector = [ self.maxmem_gb - self.minfreemem_gb, self.maxcpu - self.minfreecpu ]
        len_hf = balance_math.length(node_free_vector)

        # vector describing the resources consumed by all of the VMs on this node
        node_vm_vector = [ self.maxmem_gb - self.freemem_gb, self.maxcpu-self.freecpu ]
        len_vm = balance_math.length(node_vm_vector)

        norm_hv = balance_math.norm(node_max_vector)
        norm_hf = balance_math.norm(node_free_vector)

        if len_vm > 0:
            norm_vm = balance_math.norm(node_vm_vector)
        else:
            #sometimes, this is just zero
            norm_vm = [0,0]

        delta = balance_math.diff( node_max_vector, node_vm_vector)

        efficiency = len_vm / len_hv
        free_efficiency = len_vm / len_hf


        if report:
            logging.info("HVVector({}):          {:>.3f} [{:>.3f} {:>.3f}] [{:>.3f} {:>.3f}]".format(self.name, len_hv, *node_max_vector, *norm_hv))
            logging.info("HFVector({}):          {:>.3f} [{:>.3f} {:>.3f}] [{:>.3f} {:>.3f}]".format(self.name, len_hf, *node_free_vector, *norm_hv))
            logging.info("VMVector({}):          {:>.3f} [{:>.3f} {:>.3f}] [{:>.3f} {:>.3f}]".format(self.name, len_vm, *node_vm_vector, *norm_vm))
            logging.info("HVV*VMV({}):           {:>.3f}".format(self.name, balance_math.dot(node_max_vector, node_vm_vector)))
            logging.info("HVV*VMV/len(HVV)({}):  {:>.3f}".format(self.name, balance_math.dot(node_max_vector, node_vm_vector)/len_hv))
            logging.info("len(VMV)/len(HVV)({}): {:>.1f}% ({:>.2f}% of {:>.3f})".format(self.name, 100*efficiency, 100*free_efficiency, len_hf))
            logging.info("len(HVV-VMV)({}):      {:.3f} {}".format(self.name, balance_math.length(delta), delta ))

        if free:
            return free_efficiency

        return efficiency
