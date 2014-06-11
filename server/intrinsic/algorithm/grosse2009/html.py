import os
import numpy as np
import png

TEMPLATE = """<html>
<head>
<title>%s</title>
</head>
<body>
%s
</body>
</html>
"""

def save_png(array, fname):
    greyscale = (array.ndim == 2)
    array = (255*array).astype(np.uint32)
    m, n = array.shape[:2]
    f = open(fname, 'wb')
    writer = png.Writer(n, m, greyscale=greyscale, bitdepth=16)
    if not greyscale:
        array = array.reshape(m, n*3)
    writer.write(f, array)

class Generator:
    def __init__(self, title, dest_dir):
        self.title = title
        self.dest_dir = dest_dir
        self.items = []
        self.count = 0

    def text(self, txt):
        self.items.append(('text', txt))
        self.generate()

    def heading(self, txt):
        self.items.append(('heading', txt))
        self.generate()

    def divider(self):
        self.items.append(('divider',))
        self.generate()

    def image(self, source):
        assert type(source) == np.ndarray
        fname = 'img%d.png' % self.count
        dest_file = os.path.join(self.dest_dir, fname)
        source = 255. * source / np.max(source)
        save_png(source, dest_file)
        self.count += 1
        self.items.append(('image', fname))
        self.generate()

    def generate(self):
        body = ''
        for item in self.items:
            assert item[0] in ['text', 'heading', 'divider', 'image']
            if item[0] == 'text':
                body += '<p>' + item[1] + '</p>\n'
            elif item[0] == 'heading':
                body += '<p><h1>' + item[1] + '</p></h1>\n'
            elif item[0] == 'divider':
                body += '<hr>\n'
            elif item[0] == 'image':
                body += '<p><img src="%s"></p>\n' % item[1]
        output = TEMPLATE % (self.title, body)

        outstr = open(os.path.join(self.dest_dir, 'index.html'), 'w')
        outstr.write(output)
        outstr.close()

