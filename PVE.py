# Class for a connection to a cluster.

import sys
import logging

from VM import VM
from Node import Node

class PVE():


    def __init__(self, host=None, u=None, pw=None, excludes=None):

        import proxmoxer


        self.log = logging.getLogger(__name__)

        self.log.debug("Creating PVE instance")

        self.nodes = None
        self.nodeobj = None
        self.vms =  None
        self.excludes = excludes


        try:
            self.proxmox = proxmoxer.ProxmoxAPI(host, user=u, password=pw)

        except proxmoxer.backends.https.AuthenticationError as e:
            self.log.error("Authention error: %s" % str(e))
            sys.exit(1)

        except Exception as e:
            self.log.error("Unhandled Exception of type {} occured: {}".format(type(e), str(e)))
            sys.exit(1)
            #log.error("Authention error: %s" % str(e))


        return


    def get_nodes(self, full=False):

        self.log.debug("Getting nodes.")

        i=0

        if self.nodes is None:
            self.nodes = []
            self.nodeobj = []

            for node in self.proxmox.nodes.get():

                if node['node'] in self.excludes:
                    self.log.info("Excluding node {} on request.".format(node['node']))
                else:
                    self.nodes.append(Node(data=node))

        if full:
            return self.nodes
        else:
            return list(map(lambda n: n['node'], self.nodes))


    def get_vms(self, full=False, filter_node=None):

        self.log.debug("Getting VMs.")
        i=0
        if self.vms is None:
            self.vms = []

            for vm in self.proxmox.cluster.resources.get(type='vm'):
                self.log.debug("VM={}".format(str(vm)))
                if vm['name'] in self.excludes:
                    self.log.info('Excluding vm {} by request.'.format(vm['name']))
                else:
                    V = VM(data=vm)
                    self.vms.append(V)

        # Return a list of objects, or a list of vm names, depending
        # on the value of 'full'.  Also filter the output list by node
        # if requested
        if full:
            return [ vm for vm in self.vms if (filter_node is None or vm.node == filter_node) ]
        else:
            return [ vm.name for vm in self.vms if (filter_node is None or vm.node == filter_node) ]


