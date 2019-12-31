# -*- coding: latin-1 -*-

import time

twoup = False #True #False
pagesize = (595.28, 841.89)
date = time.strftime("%b %d, %y %H:%M")
fontsize = 11
import getpass
username = getpass.getuser()

class Font:
    def __init__(self, subtype, basefont, widths):
        self.subtype = subtype
        self.basefont = basefont
        self.widths = widths
        
    def __repr__(self):
        return '<%s>' % self.basefont

    def measure(self, s, size):
        charwidths = self.widths
        w = 0
        for c in s:
            try:
                w += charwidths[c]
            except:
                w += charwidths['m'] # XXX HACK                
        return w*size/1000.0

    def split(self, s, fontsize, width0, width1):
        # splits s such that the size of the resulting pieces is less
        # than *width*
        #
        # Achtung: wenn width kleiner als die Breite von einem Zeichen
        # ist, dann wird es kompliziert: für die erste Zeile wird ''
        # zurückgegeben, für alle weiteren wird mindestens ein Zeichen
        # eingefüllt.
        maxw = width0
        charwidths = self.widths
        r = [(0, '')]
        w = 0
        for c in s:
            try:
                _w = charwidths[c]
            except:
                _w = charwidths['m'] # XXX HACK
            _w *= fontsize/1000.0
            if w+_w > maxw:
                r.append((0, ''))
                w = 0
                maxw = width1
            a = r[-1]
            r[-1] = a[0]+_w, a[1]+c
            w += _w
        return r

_widths = {unichr(i) : 600 for i in range(256)}
COURIER = Font("Type1", "Courier", _widths)
COURIER_BOLD = Font("Type1", "Courier-Bold", _widths)
COURIER_ITALICS = Font("Type1", "Courier-Italics", _widths)

# XXX TODO: extract widths from afm-files
HELVETICA = Font("Type1", "Helvetica-Italics", _widths)
TIMES = Font("Type1", "Times", _widths)


def build_lines(pieces, max_width):
    "A piece is a tuple (string, font)"
    line = []
    width = 0
    for text, (font, fontsize) in pieces:
        add_nl = False
        for s in text.split('\n'):
            if add_nl:
                yield line
                width = 0
                line = []
            else:
                add_nl = True
                
            first = True
            for w, ss in font.split(s, fontsize, max_width-width, max_width):
                if first:
                    first = False
                else:
                    assert width <= max_width
                    yield line
                    width = 0
                    line = []
                if ss:
                    line.append((ss, (font, fontsize)))
                    width += w

def build_pages(lines, linesperpage):
    r = []
    for line in lines:
        r.append(line)
        if len(r)>=linesperpage:
            yield r
            r = []
    if r:
        yield r
        

def compute_pieces(filename):
    from pygments.formatter import Formatter
    from pygments.lexers import get_lexer_for_filename
    from pygments import token as Token
    from pygments import highlight

    style = {
        Token.Keyword : (COURIER_BOLD, fontsize),
        Token.Comment.Single : (TIMES, fontsize),
        None : (COURIER, fontsize), # default
    }
    
    class FontFormatter(Formatter):
        def format(self, tokensource, outfile, style=style):
            last = None
            l = []
            for token, text in tokensource:
                try:
                    fontinfo = style[token]
                except KeyError:
                    fontinfo = style[None]
                if fontinfo == last:
                    l[-1][0] += text
                else:
                    l.append([text, fontinfo])
                    last = fontinfo
            self.pieces = l

    formatter = FontFormatter()
    lexer = get_lexer_for_filename(filename)
    src = open(filename, 'r').read()
    highlight(src, lexer, formatter)
    return formatter.pieces


def ansi_colorize(line):
    NORMAL = '\x1b[0m'
    BOLD = '\033[1m'
    BLUE = '\033[94m'
    RED = '\033[93m'
    r = ''
    for s, (font, size) in line:
        if font == COURIER:
            r += s
        elif font == COURIER_BOLD:
            r += ''.join([BOLD, s, NORMAL])
        else:
            r += ''.join([RED, s, NORMAL])
    return r


def create_testpieces():
    import tempfile
    f = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
    name = f.name
    f.write("for a in range(10):\n    print a\n")    
    f.close()    
    pieces = compute_pieces(name)
    import os
    os.remove(name)
    return pieces


def create_randompieces():
    import random
    pieces = []
    for i in range(100):
        t = ""
        for i in range(random.randrange(10)):
            t += random.choice('abc ')
        font = random.choice([COURIER, COURIER_BOLD])
        pieces.append((t, (font, 12)))
    return pieces


def make_ref(refs):
    r = len(refs)+1, 0
    refs.add(r)
    return r


def quote(s):    
    return s.replace('\\','\\\\').replace(')','\\)').replace('(','\\(').\
        replace('\r','\\r')

def make_s(obj):
    if type(obj) == str:
        return obj
    if type(obj) == tuple:
        # we alsways interpret tuples as references!
        return '%i %i R' % obj
    if type(obj) == list:
        l = [make_s(child) for child in obj]
        return '['+(' '.join(l))+']'
    if type(obj) == dict:
        l = ['/'+make_s(k)+' '+make_s(v) for (k, v) in obj.items()]
        return '<<\n'+(' '.join(l))+' >>\n'
    if type(obj) in (int, float):
        return str(obj)
    raise Exception("Wrong type: %s" % repr(obj))


def shrink(rect, d):
    x, y, w, h = rect
    return (x+d, y+d, w-2*d, h-2*d)

def grow(rect, d):
    return shrink(rect, -d)

def create_pdf(filename=None):
    pieces = compute_pieces(filename)
    outname = 'out2.pdf'
    f = open(outname, 'wb')
    def out(obj, f=f):
        s = make_s(obj)
        f.write(s)

    fontnames = {
        COURIER : 'F1',
        COURIER_BOLD : 'F2',
        TIMES : 'F3',
        }
    xref = {} #  of tuples (number, id, position)
    pages = [] # list of content ids
    refs = set() # used references

    # geometry
    if twoup:
        # left_frame = ...
        # right_frame = ...
        # lines_per_frame = int(left_frame[3] / fontsize)
        pass
    else:
        pw, ph = pagesize
        bl = 40
        br = 40
        bt = 80
        bb = 40            
        frame = bb, bl, pw-bl-br, ph-bt-bb
        lines_per_frame = int(frame[3] / fontsize)
        lines = build_lines(pieces, frame[2])


    
    # header
    out("%PDF-1.3\n%\xC7\xEC\x8F\xA2\n")

    # object 1: catalog    
    refs.add((1, 0))
    xref[(1, 0)] = f.tell()
    out("1 0 obj\n  << /Type /Catalog\n /Pages 2 0 R >> \nendobj\n\n")

    # object 2: root pages - we write it later!
    refs.add((2, 0))

    # writing the pages    
    pagerefs = []
    groups = tuple(build_pages(lines, lines_per_frame))
    ngroups = len(groups) 
    for i, group in enumerate(groups):
        lastfontinfo = None
        cref = make_ref(refs)
        xref[cref] = f.tell()

        out("%i %i obj\n" % cref)
        lref = make_ref(refs)

        out("<< /Length %i % i R>>\n" % lref)
        out('stream\n')
        pos = f.tell()

        if twoup:
            out("0 0.5 -0.5 0 53.29 0 cm\n")
            #out("0 1 -1 0 %s 0 cm\n" % pagesize[1])
            #out("0 1 -1 0 53.2906 32.8 Tm\n") # XXX
            pass
        else:
            r = grow(frame, 2)
            out("q\n") # save state
            out("%i %i %i %i re\nS\n" % r)
            x, y, w, h = r
            d = 13 # font size header
            out("0.9 0.9 0.9 rg\n")
            out("%i %i %i %i re\nf\n" % (x, y+h, w, 2*d))
            out("Q\n") # restore state
            out("%i %i %i %i re\nS\n" % (x, y+h, w, 2*d))
            out("BT /F1 %i Tf %i %i Td (%s)Tj ET\n" % \
                (d, x+d, y+h+0.5*d, date))
            if filename:
                sw = COURIER_BOLD.measure(filename, d)
                out("BT /F2 %i Tf %i %i Td (%s)Tj ET\n" % \
                    (d+3, x+0.5*(w-sw), y+h+0.5*d, filename))
            s = "Page %i/%i" % ((i+1), ngroups)
            sw = COURIER.measure(filename, d)
            out("BT /F1 %i Tf %i %i Td (%s)Tj ET\n" % \
                (d, x+(w-sw), y+h+0.5*d, s))
            d = 11
            out("BT /F1 %i Tf %i %i Td (%s)Tj ET\n" % \
                (d, x, y-d, 'Printed by '+username))
            


        out("BT\n")
        x0, y0 = frame[:2]
        y0 += frame[3]-fontsize
        out("%s %s Td\n" % (x0, y0))
        out("%i TL\n" % fontsize)

        for l in group:
            for s, fontinfo in l:
                if fontinfo != lastfontinfo:
                    font, size = fontinfo
                    fontname = fontnames[font]
                    out("/%s %s Tf\n" % (fontname, size))
                    lastfontinfo = fontinfo
                out("(%s)Tj\n" % quote(s).encode('latin-1'))
            out("()'\n")
        out("ET")
        length = f.tell()-pos
        out("\nendstream\n")
        out("endobj\n")

        xref[lref] = f.tell()    
        out("%i %i obj\n" % lref)
        out("%i\n" % length)
        out("endobj\n")

        # directly after the content: write the page
        pref = make_ref(refs)
        pagerefs.append(pref)

        xref[pref] = f.tell()    
        out("%i %i obj\n" % pref)
        if twoup:
            rotate = "/Rotate 90\n"
        else:
            rotate = ""

        out("""
    << /Parent 2 0 R /Resources << /Font << 
        /F1 << /Encoding /WinAnsiEncoding /Type /Font 
               /BaseFont /Courier 
               /Subtype /Type1 >>
        /F2 << /Encoding /WinAnsiEncoding /Type /Font 
               /BaseFont /Courier-Bold 
               /Subtype /Type1 >>
        /F3 << /Encoding /WinAnsiEncoding /Type /Font 
               /BaseFont /Times 
               /Subtype /Type1 >>
        >>
      >>
      /MediaBox [ 0 0 595.28 841.89 ]
      %s
      /Type /Page /ProcSet [/PDF /Text /ImageB /ImageC /ImageI] 
      /Contents %i %i R 
    >>
endobj\n""" % ((rotate,)+cref))
        


    # finally writing the root pages (object 2)
    kids = ["%i %i R" % ref for ref in pagerefs]
    s = " ".join(kids)
    
    xref[(2, 0)] = f.tell()
    out("2 0 obj\n")
    w, h = (595.28, 841.89) #doc.size
    out(dict(
        Type='/Pages', Kids=kids, Count=len(kids),
        MediaBox=[0, 0, 595.28, 841.89]))
    out("endobj\n\n")
    
    # write the xref table
    startxref = f.tell()
    out('xref\n')
    out(0)
    out('%i\n' % (len(xref)+1))
    out('%010i' % 0); out('65535'); out('f\n')
    for ref in sorted(xref.keys()):
        pos = xref[ref]
        version = ref[1]
        out('%010i' % pos); out('%05i' % version); out('n\n')

    # write trailer
    out('\n')
    out('trailer\n')
    out(dict(Root='1 0 R', Size=len(xref)+1))
    out('startxref\n')
    out('%i\n' % startxref)
    out('%%EOF\n')
    
def test_00():
    "Font"
    font = COURIER
    splitter = font.split("01234567890123456789", 12, 20, 100)
    for w, s in splitter:
        print(w, font.measure(s, 12), s)

    pieces = create_randompieces()
    for l in build_lines(pieces, 100):
        print(ansi_colorize(l))

def test_01():
    for token in create_testpieces():
        print(token)

def test_02():
    pieces = create_testpieces()
    for w in (80, 160):
        print()
        for line in build_lines(pieces, w):
            print(ansi_colorize(line))

def test_03():
    pieces = compute_pieces(__file__)
    for w in (300,):
        print()
        for line in build_lines(pieces, w):
            print(ansi_colorize(line))
            
def test_04():
    filename = __file__
    create_pdf(filename)

    
if __name__=='__main__':
    import alltests
    alltests.dotests()
                    
