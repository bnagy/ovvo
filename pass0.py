#!/usr/bin/env python

import string
import os
import logging
import codecs

logger = logging.getLogger('root')
FORMAT = "<%(filename)s:%(lineno)3s> in %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

def utf8_converter(file_path, universal_endline=True):
    '''
    Convert any type of file to UTF-8 without BOM
    and using universal endline by default.

    Parameters
    ----------
    file_path : string, file path.
    universal_endline : boolean (True),
                        by default convert endlines to universal format.
    '''

    # Fix file path
    file_path = os.path.realpath(os.path.expanduser(file_path))

    # Read from file
    file_open = open(file_path)
    raw = file_open.read()
    file_open.close()

    # Decode - dosen't work for Python 3
    #raw = raw.decode(chardet.detect(raw)['encoding'])
    
    # Remove windows end line
    if universal_endline:
        raw = raw.replace('\r\n', '\n')
    # Encode to UTF-8
    raw = raw.encode('utf8')
    # Remove BOM
    if raw.startswith(codecs.BOM_UTF8):
        # Python3 - replace string (even if empty) needs to be binary encoded
        raw = raw.replace(codecs.BOM_UTF8, b'', 1)

    # Write to file
    file_open = open(file_path, 'wb')
    file_open.write(raw)
    file_open.close()
    return 0

def clean_files():
    filecount = 0
    errorcount = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if "cps" in d]
        files[:] = [f for f in files if f.lower().endswith(".xml")]
        for f in files:
            fqfn = os.path.join(root,f)
            with open(fqfn) as fh:
                try:
                    # fix up bad encoding
                    utf8_converter(fqfn)
                    logger.info("Cleaned: %s" % fqfn)
                    filecount += 1
                except Exception as e:
                    logger.info("Failed on %s -- %s" % (fqfn,e))
                    errorcount +=1
    return (filecount, errorcount)

            
if __name__ == '__main__':
    filecount, errorcount = clean_files()
    logger.info("Successfully processed %d files (failed on %d)" % (filecount, errorcount))