'''PICTUERS!'''

from PIL import Image, ImageDraw
import sys

class graphics:

    def __init__(self, filename, nodes, vms, height=None, width=None):

        self.height = height
        self.width = width
        self.filename = filename

        self.width_max = int(max([getattr(n,'maxmem') for n in nodes ])/2**30)
        self.height_max = int(max([getattr(n,'maxcpu') for n in nodes ])/2**30)

        # One image per node
        self.images = []
        self.drawings = []
        self.filenames = []
        i=0
        for node in nodes:
            self.filenames.append('{}-{}.png'.format(filename, i))
            self.images.append(Image.new('RGB', (height, width), (255,255,255)))
            self.drawings.append(ImageDraw.Draw(self.images[-1]))
            i+=1


    def box(self, x1,x2, y1,y3, title=None, border=None):

        return


    def save(self):
        for i in range(len(self.images)):
            self.images[i].save(self.filenames[i], 'PNG')
        return


    def scale(self, x, maximum, width):
        return int(x/maximum*width)


if __name__ == "__main__":
    g=graphics('output.png', None, None, height=255, width=255)
    g.draw.line((0,0)+(200,250), fill=0)

    g.image.save('output.png', "PNG")
