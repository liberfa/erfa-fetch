#!/usr/bin/env python
from __future__ import print_function


hhdrtempl = """#ifndef {libnameup}HDEF
#define {libnameup}HDEF

#include <math.h>

/*
**  - - - - - - -
**   {libnamespace} . h
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

"""


def flatten_source(srcdir, newname=None, verbose=False, addversion=None):
    import os
    import re
    import glob

    if newname is None:
        libname = srcdir
    else:
        libname = newname

    coutfn = libname + '.c'
    houtfn = libname + '.h'
    testoutfn = 'test_{fn}.c'.format(fn=libname)

    cinfns = glob.glob(os.path.join(srcdir, '*.c'))
    hinfns = glob.glob(os.path.join(srcdir, '*.h'))

    testrex = re.compile('.*t_.*?_c.c')
    for fn in cinfns:
        if testrex.match(fn):
            testinfn = fn
            break
    cinfns.remove(testinfn)

    # first make sure the macros come first so that any types/structures are
    # defined before the actual
    reordered_hinfns = []
    macrodone = False
    for hinfn in sorted(hinfns):
        if hinfn.endswith('m.h'):
            if macrodone:
                raise ValueError('Encountered *two* files of the form "*m.h" - '
                                 'can\'t proceed with this ambiguity, because '
                                 'the macro definitions have to come first.')
            reordered_hinfns.insert(0, hinfn)
            macrodone = True
        else:
            reordered_hinfns.append(hinfn)

    #now actually process the header files and combine into one
    hlines = []
    for i, fn in enumerate(reordered_hinfns):
        contentlines, hlicense = extract_content(fn)

        # first remove the header up through the end of the license comment
        for j, l in enumerate(contentlines):
            if l.startswith('*/'):
                hdrendidx = j
                break
        else:
            raise ValueError('Never found comment end in {0}'.format(fn))

        #now look for where the final #ifdef __cplusplus is, and remove all after
        ifdefidxs = [idx for idx, l in enumerate(contentlines) if l.startswith('#ifdef __cplusplus')]
        if len(ifdefidxs) > 0:
            upto = max(ifdefidxs)
        else:
            #if no cplusplus's, strip from the last #endif
            ifdefidxs = [idx for idx, l in enumerate(contentlines) if l.startswith('#endif')]
            upto = max(ifdefidxs)

        hlines.extend(contentlines[(hdrendidx + 1):upto])

    clines = []
    for fn in sorted(cinfns):
        contentlines, clicense = extract_content(fn)
        clines.extend(contentlines)

    #construct the version info string, if needed
    if addversion:
        versionstr = '//Derived from {libname} version {addversion}\n\n'.format(**locals())
    else:
        versionstr = ''

    #now save out the hlines and clines, putting in the appropriate headers and ending license
    if verbose:
        print('Writing', houtfn)
    with open(houtfn, 'w') as fw:
        if versionstr:
            fw.write(versionstr)
        fw.write(hhdrtempl.format(libnamespace=' '.join(libname),
                                  libnameup=libname.upper(),
                                  libname=libname))
        fw.write(''.join(hlines))
        #need to add an extra endif
        fw.write('#endif\n\n')
        fw.write(hlicense)

    if verbose:
        print('Writing', coutfn)
    with open(coutfn, 'w') as fw:
        if versionstr:
            fw.write(versionstr)
        fw.write(chdrtempl.format(houtfn=houtfn))
        fw.write(''.join(clines))
        fw.write(clicense)

    #finally, save out the test file with relevant modifications
    macroincludestr = '#include "{0}"'.format(houtfn.replace('.h', 'm.h'))
    angledinclstr = '#include <{0}>'.format(houtfn)
    quotedinclstr = angledinclstr.replace('<','"').replace('>','"')

    if verbose:
        print('Writing', testoutfn)
    with open(testoutfn, 'w') as fw:
        with open(testinfn) as fr:
            s = fr.read()

            if versionstr:
                fw.write(versionstr)
            fw.write(s.replace(macroincludestr, '').replace(angledinclstr, quotedinclstr))


def extract_content(fn):
    lastincl = False
    inlicense = False
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
    parser.add_argument('--newname', '-n', default=None, help='The base name '
                        'to use for the new files.  Will default to the same '
                        'as the source directory if not given.')
    parser.add_argument('--include-version', '-v', default=None, help='Gives a'
                        'version number to put at the header of the generated '
                        'files.  If not given, no version number will be '
                        'present.' )
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

    flatten_source(srcdir, args.newname, not args.quiet, args.include_version)
