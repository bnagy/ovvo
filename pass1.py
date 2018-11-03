#!/usr/bin/env python

import os
import logging
import collatinus

logger = logging.getLogger('root')
FORMAT = "<%(filename)s:%(lineno)3s> in %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)
preproc = collatinus.preprocess.Preprocessor()

def main():
    filecount = 0
    linecount = 0
    errorcount = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if "cps" in d]
        files[:] = [f for f in files if f.lower().endswith(".xml")]
        for f in files:
            fqfn = os.path.join(root,f)
            try:
                tag = preproc.process(fqfn, 'pass1')
            except Exception as e:
                logger.info("Failed on %s: %s" % (fqfn, e))
                errorcount +=1
                continue
            linecount += tag['lines']
            filecount +=1
    return (filecount, errorcount, linecount)
          

if __name__ == '__main__':
    fc, ec, lc = main()
    logger.info("Successfully processed %d files (%d lines), %d errors." % (fc,lc,ec))