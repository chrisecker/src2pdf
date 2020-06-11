# src2pdf
A sourcecode to pdf converter (to replace the a2ps-ps2pdf-sequence)

This script formats source code to nice looking pdf files. It is born out of my frustration with 
a2ps, which is not able to handle utf-8 encoded files correctly. src2pdf uses pygments and therefore
can handle all supported languages.

src2pdf does not depend upon a pdf library for creating the output. Instead output is created by 
directly printing pdf statements. 
