#!/usr/bin/env python
from __future__ import print_function

"""
This script downloads the latest SOFA, and then transforms the code to
include the appropriate copyright and function name changes.  It also
scruches all of the .c files into a single file.

In can be invoked directly on the commandline simple as::

python sofa_deriver.py

"""



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

tsthdrtempl = """#include "{outhfn}"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static int verbose = 0;

/*
**  - - - - - - - - - -
**   t e s t _ {libnmspace}
**  - - - - - - - - - -
**
**  Validate the {libname} C functions.
**
**  Each {libname} function is at least called and a usually quite basic test
**  is performed.  Successful completion is signalled by a confirming
**  message.  Failure of a given function or group of functions results
**  in error messages.
*/
"""

chdrtempl = """#include "{outhfn}"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

"""

#this is put at the *end* of the documentation comment for all C functions.
DEFAULT_INLINE_LICENSE_STR = """Licensed under a 3-clause BSD style license - see the end of this file

Copyright (c) 2013, <SOME LEGAL ORGANIZATION>
All rights reserved.
"""

#This is placed at
DEFAULT_FILE_END_LICENSE_STR = """
Copyright (c) 2013, <SOME LEGAL ORGANIZATION>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
* Neither the name of <ORG> nor the names of its contributors
  may be used to endorse or promote products derived from this software
  without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.
"""


def reprocess_files(sofatarfn, libname='erfa', func_prefix='era',
                    inlinelicensestr=DEFAULT_INLINE_LICENSE_STR,
                    endlicensestr=DEFAULT_FILE_END_LICENSE_STR,
                    verbose=True):
    import tarfile

    outcfn = libname + '.c'
    outhfn = libname + '.h'
    outtstfn = 'test_{0}.c'.format(libname)

    #first open the tar file
    tfn = tarfile.open(sofatarfn)
    try:
        hlines = []
        clines = []
        tstlines = []

        #now look for the h-files in the tar file, with sofa.h first
        htinfo = []
        for ti in tfn:
            if ti.name.endswith('.h'):
                htinfo.append(ti)
        assert len(htinfo) == 2, "should only have two .h files in the sofa archive.  Found:" + str(htinfo)

        if htinfo[0].name.endswith('sofam.h'):
            # swap order
            htinfo.append(htinfo[0])
            del htinfo[0]

        #now extract the contents of the h files for writing later
        for ti in htinfo:
            hlines.extend(reprocess_sofa_h_lines(tfn.extractfile(ti), func_prefix))
            hlines.append('\n')

        #find the .c files for processing
        testctarinfo = None  # tarinfo obj for the test's c file
        ctinfodct = {}
        for ti in tfn:
            if ti.name.endswith('.c'):
                if ti.name.endswith('t_sofa_c.c'):
                    testctarinfo = ti
                else:
                    ctinfodct[ti.name.split('/')[-1]] = ti

        #now process the c files in lexical sort order for writing later
        for nm in sorted(ctinfodct):
            fr = tfn.extractfile(ctinfodct[nm])
            clines.extend(reprocess_sofa_c_lines(fr, func_prefix, inlinelicensestr))

        #finally, get out the tests C-file, but without the SOFA-using header

        inhdr = True
        for l in tfn.extractfile(testctarinfo):
            if inhdr:
                if l.startswith('*/'):
                    inhdr = False
            else:
                replln = l.replace('iau', func_prefix).replace('SOFA', libname.upper()).replace('sofa', libname)
                tstlines.append(replln)

        #turn the license string into a C comment
        endlicensestr = '**  ' + '\n**  '.join(endlicensestr.split('\n'))
        endlicensestr = '/*\n' + endlicensestr + '\n*/\n'

        #now write h- and c-files, and the testing file
        if verbose:
            print('Writing headers to ' + outhfn)
        with open(outhfn, 'w') as fw:
            #first the header
            fw.write(hhdrtempl.format(libname=libname.upper(), libnmspace=' '.join(libname)))
            for l in hlines:
                fw.write(l)
            fw.write('\n')
            fw.write(endlicensestr)
            fw.write('\n#endif\n\n')

        if verbose:
            print('Writing C functions to ' + outcfn)
        with open(outcfn, 'w') as fw:
            fw.write(chdrtempl.format(outhfn=outhfn))  # does not need any substitutions, just imports
            for l in clines:
                fw.write(l)
            fw.write('\n')
            fw.write(endlicensestr)

        if verbose:
            print('Writing tests to ' + outtstfn)
        with open(outtstfn, 'w') as fw:
            #fill in all the missing header
            fw.write(tsthdrtempl.format(libname=libname.upper(), libnmspace=' '.join(libname), outhfn=outhfn))

            for l in tstlines:
                fw.write(l)
            fw.write('\n')
    finally:
        tfn.close()


def reprocess_sofa_h_lines(inlns, func_prefix):
    outlns = []
    inhdr = True  # everything up to and including the includes

    for l in inlns:
        if inhdr:
            if l.startswith('#include'):
                inhdr = 'incl'
            elif inhdr == 'incl':
                inhdr = False
        elif l.startswith('/*----------------------------------------------------------------------'):
            #in license section at end of file
            outlns.append('\n')
            break
        else:
            outlns.append(l.replace('iau', func_prefix))

    if outlns[-3].startswith('#endif'):
        outlns = outlns[:-3]

    return outlns


def reprocess_sofa_c_lines(inlns, func_prefix, inlinelicensestr):
    spaced_prefix = ' '.join(func_prefix)

    outlns = []
    inhdr = True  # start inside the header before the function def'n
    replacedprefix = False  # indicates if the "iau" line has been hit
    replacedspacedprefix = False  # indicates if the "i a u" line has been hit
    incopyright = False  # indicates being inside the copyright/revision part of the doc comment of the SOFA function

    for l in inlns:
        if inhdr:
            # *don't* include the header because it has includes
            # that are shared in the to-be-created file

            if (not replacedprefix) and 'iau' in l:
                # this is the function definition and the end of the header
                outlns.append(l.replace('iau', func_prefix))
                replacedprefix = True
                inhdr = False
        elif (not replacedspacedprefix) and 'i a u' in l:
            outlns.append(l.replace('i a u', spaced_prefix))
            replacedspacedprefix = True
        elif incopyright:
            # skip the copyright/versioning section unless it's the end
            if l.startswith('*/'):  # indicates end of the doc comment
                incopyright = False
                outlns.append(l)
        elif l.startswith('/*----------------------------------------------------------------------'):
            #this means we are in the license section, so we are done
            #except for the final close-bracket always comes after the
            #license section
            outlns.append('}\n')
            break
        elif l.startswith('**  This revision:'):
            incopyright = True
            #start of the copyright/versioning section - need to strip this because it contains SOFA references.

            #but put in the correct inline license instead
            if inlinelicensestr:
                inlinelicensestr = '**  ' + inlinelicensestr
                outlns.append('\n**  '.join(inlinelicensestr.split('\n')))
                outlns.append('\n')
        else:
            # need to replace 'iau' b/c other SOFA functions are often called
            outlns.append(l.replace('iau', func_prefix))

    return outlns


def download_sofa(url=None, dlloc='.', verbose=True):
    """
    Downloads the latest version of SOFA (or one specified via `url`) to
    the `dlloc` directory.

    If `extract`, also extract that .tar.gz file
    """
    import os
    import urllib

    if url is None:
        url = _find_sofa_url_on_web_page()

    fn = url.split('/')[-1]
    if not os.path.isdir(dlloc):
        raise ValueError('Requested dlloc {0} is not a directory'.format(dlloc))

    fnpath = os.path.join(dlloc, fn)
    if verbose:
        print('Downloading {fn} to {fnpath}'.format(fn=fn, fnpath=fnpath))
    retfn, headers = urllib.urlretrieve(url, fnpath)

    return retfn



def _find_sofa_url_on_web_page(url='http://www.iausofa.org/current_C.html'):
    """
    Finds and returns the download URL for the latest C SOFA.
    """
    import urllib2
    from HTMLParser import HTMLParser

    # create a subclass and override the handler methods
    class SOFAParser(HTMLParser):
        def __init__(self):
            self.matched_urls = []
            HTMLParser.__init__(self)

        def handle_starttag(self, tag, attrs):
            if tag == 'a' and attrs[-1][-1].endswith('.tar.gz'):
                self.matched_urls.append(attrs[-1][-1])

    parser = SOFAParser()
    u = urllib2.urlopen(url)
    try:
        for l in u:
            parser.feed(l)
    finally:
        u.close()

    baseurl = '/'.join(url.split('/')[:-1])
    fullurls = [(baseurl + m) for m in parser.matched_urls]

    if len(fullurls) != 1:
        raise ValueError('Found *multiple* possible downloads: ' +
                         str(fullurls))

    return fullurls[0]


if __name__ == '__main__':
    import sys
    import glob
    import tarfile
    import argparse

    parser = argparse.ArgumentParser(description='Generates code derived from SOFA.')
    parser.add_argument('sofafile', nargs='?', default=None, help='The sofa '
                        '.tar.gz file to use.  If absent, the current '
                        'directory will be searched, and if still absent, the '
                        'latest sofa will be downloaded from the web.')
    parser.add_argument('--download', '-d', default=False, action='store_true',
                        help='Download the latest SOFA regardless regardless '
                        'of whether there is already a SOFA in the current '
                        'directory')
    parser.add_argument('--quiet', '-q', default=False, action='store_true',
                        help='Print less info to the terminal.')
    args = parser.parse_args()

    if args.download:
        if args.sofafile is not None:
            print('Cannot give both --download and sofafile!', file=sys.stderr)
            sys.exit(1)
        sofatarfn = download_sofa(verbose=not args.quiet)
    elif args.sofafile is not None:
        try:
            #try to open the file as a tar file
            f = tarfile.open(args.sofafile)
            f.close()
        except (IOError, tarfile.ReadError) as e:
            print('requested sofafile "{0}" is not a valid tar file: '
                  '"{1}"'.format(args.sofafile, e), file=sys.stderr)
            sys.exit(1)
        #all is ok - use the file below
        sofatarfn = args.sofafile
    else:
        lstar = glob.glob('sofa_c*.tar.gz')

        if len(lstar) > 1:
            print("Found multiple sofa_c*.tar.gz files: {0} - can't pick which "
                  "one to use:".format(lstar), file=sys.stderr)
            sys.exit(1)
        elif len(lstar) == 0:
            if not args.quiet:
                print('Did not find any sofa_c*.tar.gz files - downloading.')
            sofatarfn = download_sofa(verbose=not args.quiet)
        else:
            sofatarfn = lstar[0]  # there is only one
    if not args.quiet:
        print('Using sofa tarfile "{0}" for reprocessing'.format(sofatarfn))
    reprocess_files(sofatarfn, verbose=not args.quiet)
