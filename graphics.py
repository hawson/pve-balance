'''PICTUERS!'''

import sys
import logging
from PIL import Image, ImageDraw, ImageFont

class graphics:

    def __init__(self,  nodes, vms, height=None, width=None):

        self.log = logging.getLogger(__name__)

        self.height = height
        self.width = width


        # Find the largest resource values for X (memory) and Y (CPUs)
        # across all nodes, so that they can be scaled to the requested
        # image dimensions.

        xs = [getattr(n,'maxmem_gb') for n in nodes ]
        ys = [getattr(n,'maxcpu') for n in nodes ]

        self.x_max = max(xs)
        self.y_max = max(ys)

        self.log.debug("{}: X={}".format(self.x_max, str(xs)))
        self.log.debug("{}: Y={}".format(self.y_max, str(ys)))

        # One image per node
        self.image = {}

        self.drawings = {}
        self.filenames = {}
        self.vm_map = {}

        self.px_per_mem_gb = width / self.x_max
        self.px_per_cpu  = height / self.y_max

        self.log.debug("MaximumX: {:>.1f}/{:>.1f}px MaximumY: {}/{:>.1f}px".format(self.x_max, self.px_per_mem_gb, self.y_max, self.px_per_cpu))

        for node in nodes:

            # width and height in px of the image for this node.
            w = int(node.maxmem_gb / self.x_max * width)
            h = int(node.maxcpu / self.y_max * height)

            cpu_y = int(node.minfreecpu/node.maxcpu * height)
            mem_x = int(node.minfreemem/node.maxmemGB * width)

            self.log.info("Scaling Mem({:.1f})/CPU({}) -> {}x{} (of {}x{})".format(
                node.maxmem_gb, node.maxcpu, w,h, width, height))
            self.log.info("  Thresholds at mem:({}-{})={} cpu:({}-{})={}".format(w,mem_x,w-mem_x, h,cpu_y,h-cpu_y))
            self.log.info("1xCPU={} 1xMemGB={}".format(self.px_per_cpu, self.px_per_mem_gb))

            # Create a new image
            self.image[node.name] = {
                'img': Image.new('RGB', (w, h), (255,255,255)),
                'filename': '{}.png'.format(node.name),
                'px': 0,
                'py': 0,
            }

            # Make a drawing canvas
            self.image[node.name]['draw'] = ImageDraw.Draw(self.image[node.name]['img'])

            # minimum lines
            self.image[node.name]['draw'].line((0,h-cpu_y, w,h-cpu_y), fill='#a00')  # min CPU line
            self.image[node.name]['draw'].line((w-mem_x,0, w-mem_x,h), fill='#00a')  # min MEM line

            # labels for minimum lines
            self.image[node.name]['draw'].text((int(w/2), h-cpu_y), "CPU", align="center", directon='ttb', fill=(0,0,0,255))
            self.image[node.name]['draw'].text((w-mem_x, int(h/2)), "MEM", align="center", directon='ltr', fill=(0,0,0,255))

            self.log.debug("{}: {}x{}".format(self.image[node.name]['filename'], w, h ))


            for vm in node.allocated_vms:

                # Note:  we cannot use "vm.node", since that's the "old" placement, not the new packed one one

                ox = self.image[node.name]['px']
                oy = self.image[node.name]['py']

                self.image[node.name]['px'] += vm.maxmem_gb * self.px_per_mem_gb
                self.image[node.name]['py'] += vm.maxcpu   * self.px_per_cpu

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





    def save(self):
        for node in self.image:
            fname = self.image[node]['filename']
            self.image[node]['img'].save(fname, 'PNG')


if __name__ == "__main__":
    g=graphics('output.png', None, None, height=255, width=255)
    g.draw.line((0,0)+(200,250), fill=0)

    g.image.save('output.png', "PNG")
