ERAS
====

Essential Routines for AStronomy

This repository contains the tools necessary for downloading the latest 
Standards of Fundamental Astronomy (SOFA) library and converting it to ERAS, 
a BSD-licensed code.

To download the latest SOFA and use it to generate ERAS source code, just do:

    python sofa_deriver.py

To see more options, do ``python sofa_deriver.py --help``

To compile and execute the tests, do:

    [CC] eras.c test_eras.c -o test_eras
    ./test_eras --verbose

where ``[CC]`` is replaced by your preferred C compiler.