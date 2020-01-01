# -*- coding:latin-1 -*-

import src2pdf

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
