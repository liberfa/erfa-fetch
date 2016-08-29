Essential Routines for Fundamental Astronomy (ERFA)
===================================================

This repository contains the tools necessary for downloading the latest
Standards of Fundamental Astronomy (SOFA) library and converting it to ERFA,
a BSD-licensed code.

To download the latest SOFA and use it to generate ERFA source code, just do:

    python sofa_deriver.py

which should generate an `erfa` directory with all the source code.

To see more options, do ``python sofa_deriver.py --help``

Testing
-------

To compile and execute the tests, do:

    [CC] erfa/*.c -Ierfa -lm -o test_erfa
    ./test_erfa --verbose

where ``[CC]`` is replaced by your preferred C compiler.

Making single-file versions
---------------------------

`source_flattener.py` is provided to condense the source code into
a single file.  Just do:

    python source_flattener.py

to get out `erfa.c` and `erfa.h`.  In general you probably do not want to
do this in the `erfa-fetch` repository, though, as it won't include any
bugfixes in ERFA that have not yet been included in SOFA.  Instead, do this
in the actual `erfa` repository:

    python source_flattener.py src -n erfa
