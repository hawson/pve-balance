'''PICTUERS!'''

from PIL import Image, ImageDraw, ImageFont
import sys
import logging

class graphics:

    def __init__(self,  nodes, vms, height=None, width=None):

        self.log = logging.getLogger(__name__)

        self.height = height
        self.width = width

        self.x_max = max([getattr(n,'maxmem') for n in nodes ])
        self.y_max = max([getattr(n,'maxcpu') for n in nodes ])

        # One image per node
        self.image = {}

        self.drawings = {}
        self.filenames = {}
        self.vm_map = {}

        i=0

        for node in nodes:

            w = int(node.maxmem / self.x_max * width)
            h = int(node.maxcpu / self.y_max * height)

            cpu_y = int(node.minfreecpu/node.maxcpu * height)
            mem_x = int(node.minfreemem/node.maxmem * width)

            # Create a new image
            self.image[node.name] = {
                'img': Image.new('RGB', (w, h), (255,255,255)),
                'filename': '{}.png'.format(node.name),
                'px': 0,
                'py': 0,
            }

            # Make a drawing canvas
            self.image[node.name]['draw'] = ImageDraw.Draw(self.image[node.name]['img'])

            self.image[node.name]['draw'].line((0,h-cpu_y, w,h-cpu_y), fill='#a00')  # min CPU line
            self.image[node.name]['draw'].line((w-mem_x,0, w-mem_x,h), fill='#00a')  # min MEM line

            self.image[node.name]['draw'].text((int(w/2), h-cpu_y), "CPU", align="center", directon='ttb', fill=(0,0,0,255))
            self.image[node.name]['draw'].text((w-mem_x, int(h/2)), "MEM", align="center", directon='ltr', fill=(0,0,0,255))

            self.log.debug("{}: {}x{}".format(self.image[node.name]['filename'], w, h ))


            for vm in node.allocated_vms:

                # Note:  we cannot use "vm.node", since that's the "old" placement, not the new one

                ox = self.image[node.name]['px']
                oy = self.image[node.name]['py']

                self.image[node.name]['px'] += self.scale(vm.maxmem, self.x_max, width)
                self.image[node.name]['py'] += self.scale(vm.maxcpu, self.y_max, width)

                px = self.image[node.name]['px']
                py = self.image[node.name]['py']

                self.log.debug("Drawing {} on {} ({}x{})+({}x{})".format(vm.name, node.name, ox,oy, px, py))
                self.log.debug("        {} area={} area_perc={:.3f} score={}".format(vm.name, vm.area(), vm.area_perc(), vm.score()))

                self.image[node.name]['draw'].rectangle( 
                        [(ox, oy), (px, py)], 
                        outline=(0,0,0),
                        fill=None
                        )
                self.image[node.name]['draw'].text( (ox+2,oy+1), vm.name, fill=(0,0,0,255))



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
