#!/usr/bin/env python
from __future__ import print_function


def download_sofa(url=None, dlloc='.', extract=False):
    """
    Downloads the latest version of SOFA (or one specified via `url`) to
    the `dlloc` directory.

    If `extract`, also extract that .tar.gz file
    """
    import os
    import urllib
    import tarfile

    if url is None:
        url = _find_sofa_url_on_web_page()

    fn = url.split('/')[-1]
    if not os.path.isdir(dlloc):
        raise ValueError('Requested dlloc {0} is not a directory'.format(dlloc))

    fnpath = os.path.join(dlloc, fn)
    print('Downloading {fn} to {fnpath}'.format(fn=fn, fnpath=fnpath))
    urllib.urlretrieve(url, fnpath)

    if extract:
        tar = tarfile.open(fnpath)
        try:
            tar.extractall(dlloc)
        finally:
            tar.close()


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


def find_sofa_files(suffix='.c', rootdir='.'):
    import os

    sofadir = os.path.join(rootdir, 'sofa')
    if not os.path.isdir(sofadir):
        raise ValueError('{0} is not a valid directory'.format(sofadir))

    versdir = os.path.join(sofadir, os.listdir(sofadir)[0])
    cdir = os.path.join(versdir, 'c')
    srcdir = os.path.join(cdir, 'src')

    if not os.path.isdir(srcdir):
        raise ValueError('{0} is not a valid directory'.format(srcdir))

    fullfns = [os.path.join(srcdir, fn) for fn in os.listdir(srcdir) if fn.endswith(suffix)]
    return fullfns


def reprocess_c_files(fns, outfn='sofa.c', func_prefix='xxx', licensestr=''):
    reslines = []
    spaced_prefix = ' '.join(func_prefix)

    for fn in fns:
        with open(fn) as fr:
            for l in fr:
                if l.startswith('/*----------------------------------------------------------------------'):
                    reslines.append(licensestr)
                    reslines.append('\n//---------------------------END OF FUNCTION----------------------------\n\n\n')
                    break
                    #this means we are in the license section, so we are done
                if "#include" in l:
                    continue  # skip includes
                reslines.append(l.replace('iau', func_prefix).replace('i a u', spaced_prefix))


    with open(outfn, 'w') as fw:
        for l in reslines:
            fw.write(l)


if __name__ == '__main__':
    import argparse

    #download_sofa(extract=True)
    reprocess_c_files(find_sofa_files('.c'), outfn='sofa.c',licensestr='')