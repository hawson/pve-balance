'''PICTUERS!'''

from PIL import Image, ImageDraw
import sys
import logging

class graphics:

    def __init__(self, pack, filename, nodes, vms, height=None, width=None):

        self.log = logging.getLogger(__name__)

        self.height = height
        self.width = width
        self.filename = filename

        self.x_max = int(max([getattr(n,'maxmem') for n in nodes ]))
        self.y_max = int(max([getattr(n,'maxcpu') for n in nodes ]))

        # One image per node
        self.image = {}

        self.drawings = {}
        self.filenames = {}
        self.vm_map = {}

        i=0

        for node in nodes:

            w = int(node.maxmem / self.x_max * width)
            h = int(node.maxcpu / self.y_max * height)

            self.image[node.name] = {
                'img': Image.new('RGB', (w, h), (255,255,255)),
                'filename': '{}.png'.format(node.name),
                'px': 0,
                'py': 0,
            }
            self.image[node.name]['draw'] = ImageDraw.Draw(self.image[node.name]['img'])

            i+=1
            self.log.debug("{}: {}x{}".format(self.image[node.name]['filename'], w, h ))



            for vm in node.allocated_vms:

                # Note:  we cannot use "vm.node", since that's the "old" placement, not the new one

                ox = self.image[node.name]['px']
                oy = self.image[node.name]['py']

                self.log.debug("Drawing {} on {} ({}x{})".format(vm.name, vm.node, ox,oy))

                self.image[node.name]['px'] += self.scale(vm.maxmem, self.x_max, width) + 1
                self.image[node.name]['py'] += self.scale(vm.maxcpu, self.y_max, width) + 1
                self.image[node.name]['draw'].rectangle( 
                        [(ox, oy), (self.image[node.name]['px'], self.image[node.name]['py'])], 
                        outline=(0,0,0),
                        fill=None
                        )



    def box(self, x1,x2, y1,y3, title=None, border=None):

        return


    def save(self):
        for node in self.image:
            fname = self.image[node]['filename']
            self.image[node]['img'].save(fname, 'PNG')
        return


    def scale(self, x, maximum, width):
        return int(x/maximum*width)


if __name__ == "__main__":
    g=graphics('output.png', None, None, height=255, width=255)
    g.draw.line((0,0)+(200,250), fill=0)

    g.image.save('output.png', "PNG")
