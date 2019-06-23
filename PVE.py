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

        i=0

        if self.nodes is None:
            self.nodes = []
            self.nodeobj = []

            for node in self.proxmox.nodes.get():

                if node['node'] in self.excludes:
                    self.log.info("Excluding node {} on request.".format(node['node']))
                else:
                    self.nodes.append(node)
                    N = Node(data=node)
                    N.show()
                    self.nodeobj.append( Node(data=node))


        if full:
            return self.nodes
        else:
            return list(map(lambda n: n['node'], self.nodes))






