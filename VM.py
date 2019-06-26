# class for VMs

import logging

import functools

@functools.total_ordering
class VM:

    fmt='{vmid:5>} {name:>20}{state} {cpu}/{maxcpu}(%{cpu_perc}) {maxmem}G {node} score: {score}'


    weight = {
        'mem':  1.0,
        'disk': 0.0,   # This will be normalized to GB (not bytes
        'cpu':  1.0,   # CPU utilization as "fraction_as_percentage",
        'net':  1.0,   # This will be normalized to MB/sec (not Mbps)
        'ncpu': 1.0,   # Scale down total CPU count, bias more towards usage
    }


    def __init__(self, data=None, bias=0.0):
        if data:
            for k,v in data.items():
                setattr(self, k ,v)
            self.name = data['name']

        self.log = logging.getLogger(__name__)
        self.bias = bias

    def __str__(self):
        return self.name

    def __eq__(self,other):
        return( (self.status, self.name, self.vmid)  == ( other.status, other.name, other.vmid) )

    def __lt__(self,other):
        return( (self.status, self.name, self.vmid)   < ( other.status, other.name, other.vmid) )


    def get_node(self, node):
        if self.node == node:
            return True
        return False


    def show(self, format=None):
        print(VM.fmt.format(
            vmid     = self.vmid,
            name     = self.name,
            state    = ' ' if self.status == 'running' else '*',
            cpu      = '{:>03.1f}'.format(self.cpu),
            maxcpu   = '{:>2}'.format(self.maxcpu),
            node     = '{:>4}'.format(self.node),
            cpu_perc = '{:>2.0f}'.format(float( float(self.cpu)/float(self.maxcpu )*100)),
            maxmem   = '{:>3.0f}'.format(float(self.maxmem / 2**30)),
            score    = self.score(full=True),
        ))

    def area_perc(self):
        return float(self.mem / 2**30) * self.cpu

    def area(self):
        return float(self.maxmem / 2**30) * self.maxcpu

    def score(self, biased=True, full=False):

        vm_name = self.name

        score = 0.0

        scores = {
            'cpu':  self.cpu    * VM.weight['cpu'],
            'mem':  self.maxmem * VM.weight['mem'] / 2**30,
            'net':  0.0         * VM.weight['net'],
            'disk': 0.0         * VM.weight['disk'],
            'bias': self.bias,
        }

        score = sum(scores.values())


        if full:
            return '{:< 6.3f} = {:5.3f} + {:5.3f} + {:3.1f}'.format(
                    score,
                    scores['cpu'],
                    scores['mem'],
                    scores['bias'],
                    )
        else:
            return '{:< 6.3f}'.format(score)

