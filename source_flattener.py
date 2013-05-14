#!/usr/bin/env python
from __future__ import print_function


hhdrtempl = """#ifndef {libname}HDEF
#define {libname}HDEF

#include <math.h>

/*
**  - - - - - - -
**   {libnmspace} . h
**  - - - - - - -
**
**  Prototype function declarations and macros for {libname} library.
**
*/
"""

chdrtempl = """#include "{houtfn}"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

"""


def flatten_source(srcdir, verbose=False):
    import os
    import re
    import glob

    coutfn = srcdir + '.c'
    houtfn = srcdir + '.h'
    testoutfn = 'test_{srcdir}.c'.format(srcdir=srcdir)

    cinfns = glob.glob(os.path.join(srcdir, '*.c'))
    hinfns = glob.glob(os.path.join(srcdir, '*.h'))

    testrex = re.compile('.*t_.*?_c.c')
    for fn in cinfns:
        if testrex.match(fn):
            testinfn = fn
            break
    cinfns.remove(testinfn)

    #first process the header files and combine into one
    hlines = []
    for fn in hinfns:
        contentlines, hlicense = extract_content(fn)
        hlines.extend(contentlines)

    clines = []
    for fn in cinfns:
        contentlines, clicense = extract_content(fn)
        clines.extend(contentlines)

    #now save out the hlines and clines, putting in the appropriate headers and ending license
    if verbose:
        print('Writing', houtfn)
    with open(houtfn, 'w') as fw:
        fw.write(hhdrtempl.format(libnmspace=' '.join(srcdir), libname=srcdir))
        fw.write(''.join(hlines))
        fw.write(hlicense)

    if verbose:
        print('Writing', coutfn)
    with open(coutfn, 'w') as fw:
        fw.write(chdrtempl.format(houtfn=houtfn))
        fw.write(''.join(clines))
        fw.write(clicense)

    #finally, save out the test file
    if verbose:
        print('Writing', testoutfn)
    with open(testoutfn, 'w') as fw:
        with open(testinfn) as fr:
            fw.write(fr.read())


def extract_content(fn):
    lastincl = False
    inlicense = True
    lines = []
    licenselines = []
    with open(fn) as f:
        for l in f:
            if l.startswith('#include'):
                lastincl = True
            elif lastincl and l.strip() in ('', '**'):
                # don't include unnecessary blank lines
                lastincl = False
            elif inlicense:
                licenselines.append(l)
            elif l.startswith('/*----------------------------------------------------------------------'):
                lines.append('\n')
                licenselines.append(l)
                inlicense = True
            else:
                lines.append(l)
                lastincl = False

    return lines, ''.join(licenselines)


if __name__ == '__main__':
    import os
    import sys
    import glob
    import argparse

    parser = argparse.ArgumentParser(description='Combines the sofa-derived '
                                                 'source code into a single C '
                                                 'and header file.')
    parser.add_argument('srcdir', nargs='?', default=None, help='The directory '
                        'to find the source code in. If not, all directories '
                        'under the current one will be searched for something '
                        'with .h files that look right.')
    parser.add_argument('--quiet', '-q', default=False, action='store_true',
                        help='Print less info to the terminal.')
    args = parser.parse_args()

    if args.srcdir is None:
        dirfns = [fn for fn in os.listdir('.') if os.path.isdir(fn)]
        validdirs = []
        for dirfn in dirfns:
            hfiles = glob.glob(os.path.join(dirfn, '*.h'))
            if len(hfiles) == 2:
                flens = [len(fn) for fn in hfiles]
                sofainname = [('sofa' in fn.lower()) for fn in hfiles]
                if min(flens) == (max(flens) - 1) and not any(sofainname):
                    validdirs.append(dirfn)

        if len(validdirs) < 1:
            print('No srcdir was given and no directory that looked like it '
                  'was SOFA-derived was found.')
            sys.exit(1)
        if len(validdirs) > 2:
            print('No srcdir was given and multiple directories were found '
                  'that look SOFA-derived: ' + str(validdirs))
            sys.exit(1)

        srcdir = validdirs[0]
    else:
        srcdir = args.srcdir

    flatten_source(srcdir, not args.quiet)
