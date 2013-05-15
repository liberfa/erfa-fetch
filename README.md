Essential Routines for Fundamental Astronomy (ERFA)
===================================================

This repository contains the tools necessary for downloading the latest
Standards of Fundamental Astronomy (SOFA) library and converting it to ERFA,
a BSD-licensed code.

To download the latest SOFA and use it to generate ERFA source code, just do:

    python sofa_deriver.py

which should generate an `erfa` directory with all the source code.

To see more options, do ``python sofa_deriver.py --help``

To compile and execute the tests, do:

    [CC] erfa/*.c -lm -o test_erfa
    ./test_erfa --verbose

where ``[CC]`` is replaced by your preferred C compiler.