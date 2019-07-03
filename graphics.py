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

        self.px_per_mem_gb = width / self.x_max
        self.px_per_cpu  = height / self.y_max

        self.log.debug("MaximumX: {:>.1f}/{:>.1f}px MaximumY: {}/{:>.1f}px".format(self.x_max, self.px_per_mem_gb, self.y_max, self.px_per_cpu))

        for node in nodes:

            # width and height in px of the image for this node.
            w = int(node.maxmem_gb / self.x_max * width)
            h = int(node.maxcpu / self.y_max * height)

            # minfree lines for CPU (Y-axis, so horiz. line) and MEM (X-axis, so vert. line)
            cpu_y = node.minfreecpu * self.px_per_cpu
            mem_x = node.minfreemem/2**30 * self.px_per_mem_gb
            #cpu_y = int(node.minfreecpu/node.maxcpu * height)
            #mem_x = int(node.minfreemem/2**30/node.maxmem_gb * width)

            self.log.info("Scaling Mem({:.1f})/CPU({}) -> {}x{} (of {}x{})".format(
                node.maxmem_gb, node.maxcpu, w,h, width, height))
            self.log.info("  Thresholds at mem:({}-{})={} cpu:({}-{})={}".format(w,mem_x,w-mem_x, h,cpu_y,h-cpu_y))
            self.log.info("1xCPU={} 1xMemGB={}".format(self.px_per_cpu, self.px_per_mem_gb))

            self.image_setup(node, w, h, mem_x, cpu_y)


            # Loop over all of the VMs that have been allocated to this node.
            for vm in node.allocated_vms:

                # Note:  we cannot use "vm.node" to get the name of the node we are dealing with,
                # since that's the "old" placement, not the new packed one one

                # Old bottom-right corners become new top-left corners
                ox = self.image[node.name]['px']
                oy = self.image[node.name]['py']

                # New bottom-right corners are the px_per_metric * the_metrics
                self.image[node.name]['px'] += vm.maxmem_gb * self.px_per_mem_gb
                self.image[node.name]['py'] += vm.maxcpu   * self.px_per_cpu

                # update shorthand variables.
                px = self.image[node.name]['px']
                py = self.image[node.name]['py']

                self.log.debug("Drawing {} on {} ({}x{})+({}x{})".format(vm.name, node.name, ox,oy, px, py))
                self.log.debug("        {} area={} area_perc={:.3f} score={}".format(vm.name, vm.area(), vm.area_perc(), vm.score()))

                # Draw a box for the VM In question, and label it.
                self.draw_vm(node.name, vm.name, ox, oy, px, py)


    def draw_vm(self, node_name, vm_name, ox, oy, px, py):
        self.image[node_name]['draw'].rectangle(
            [(ox, oy), (px, py)], 
            outline=(0,0,0),
            fill=None
        )
        self.image[node_name]['draw'].text( (ox+2,oy+1), vm_name, fill=(0,0,0,255))



    def image_setup(self, node, w, h, mem_x, cpu_y, cpu_ticks = 5, mem_gb_ticks = 5):
        '''Basic image creation and setup.  Place small and medium tick marks periodically.'''

        # Create a new image
        self.image[node.name] = {
            'img': Image.new('RGB', (w, h), (255,255,255)),
            'filename': '{}.png'.format(node.name),
            'px': 0,
            'py': 0,
            'draw': None,
        }

        # Make a drawing canvas
        self.image[node.name]['draw'] = ImageDraw.Draw(self.image[node.name]['img'])

        # tick marks
        base_tick_length_px = 10

        gb = 0
        while gb < node.maxmem_gb:
            x = gb * self.px_per_mem_gb
            tick_len = base_tick_length_px
            if 0 == (gb % mem_gb_ticks):
                tick_len *= 2
            self.image[node.name]['draw'].line((x,0, x, tick_len), fill='#00a')  # MEM tickmark
            self.image[node.name]['draw'].line((x,h, x, h-tick_len), fill='#00a')  # MEM tickmark
            gb += 1

        cpu = 0
        while cpu < node.maxcpu:
            y = cpu * self.px_per_cpu
            tick_len = base_tick_length_px
            if 0 == (cpu % cpu_ticks):
                tick_len *= 2
            self.image[node.name]['draw'].line((0,y, tick_len, y), fill='#00a')  # MEM tickmark
            self.image[node.name]['draw'].line((w,y, w-tick_len, y), fill='#00a')  # MEM tickmark
            cpu += 1




        # minimum lines
        self.image[node.name]['draw'].line((0,h-cpu_y, w,h-cpu_y), fill='#a00')  # min CPU line
        self.image[node.name]['draw'].line((0,h-cpu_y+1, w,h-cpu_y+1), fill='#a00')  # min CPU line

        self.image[node.name]['draw'].line((w-mem_x,0, w-mem_x,h), fill='#00a')  # min MEM line
        self.image[node.name]['draw'].line((w-mem_x+1,0, w-mem_x+1,h), fill='#00a')  # min MEM line

        # labels for minimum lines
        self.image[node.name]['draw'].text((int(w/2), h-cpu_y+1), "Min CPU Limit", align="center", directon='ttb', fill=(0,0,0,255))
        self.image[node.name]['draw'].text((w-mem_x+3, int(h/2)), "Min MEM", align="left", directon='ltr', fill=(0,0,0,255))
        self.image[node.name]['draw'].text((w-mem_x+3, int(h/2)+10), "Limit", align="left", directon='ltr', fill=(0,0,0,255))

        self.log.debug("{}: {}x{}".format(self.image[node.name]['filename'], w, h ))





    def save(self):
        for node in self.image:
            fname = self.image[node]['filename']
            self.image[node]['img'].save(fname, 'PNG')


if __name__ == "__main__":
    g=graphics('output.png', None, None, height=255, width=255)
    g.draw.line((0,0)+(200,250), fill=0)

    g.image.save('output.png', "PNG")
