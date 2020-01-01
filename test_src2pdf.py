# -*- coding:latin-1 -*-

import src2pdf


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
