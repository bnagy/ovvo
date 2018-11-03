#!/usr/bin/env python

import string
import os
import hashlib
import re
import logging
import json
import textwrap
import io
import collatinus

logger = logging.getLogger('root')
FORMAT = "<%(filename)s:%(lineno)3s> in %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)
cleaner = collatinus.clean.Cleaner()

def process():

    filecount = 0
    linecount = 0
    failed = 0
    if not os.path.exists('pass2'):
        os.makedirs('pass2')

    for root, dirs, files in os.walk('pass1'):
        files[:] = [f for f in files if f.lower().endswith("df01bb99.txt")]
        for f in files:
            fqfn = os.path.join(root,f)
            try:
                basename = os.path.splitext(f)[0]
                fqtagname = os.path.join(root, "%s.json" % basename)
                with open(fqtagname) as th:
                    tag = json.load(th)
                    logger.info("[file]   %s" % fqfn)
                    logger.info("[work]   %s -- %s" % (tag['author'], tag['title']))

                with open(fqfn, mode='r', encoding='utf-8') as fh:
                    text = fh.read()

                sents = cleaner.tokenize_sentences(text)
                if not any(sents):
                    logger.info("No remaining sentences. Not writing any output.")
                    continue

                tag['pass1'] = fqfn
                tag['lines'] = len(sents)
                text = '\n'.join(sents)
                h = hashlib.sha256(text.encode('utf-8'))
                hex_dig = h.hexdigest()

                linecount += tag['lines']

                try:
                    fname = "%s.txt" % hex_dig
                    tagname = "%s.json" % hex_dig
                    with open(os.path.join('pass2',fname),"wb") as f:
                        f.write(text.encode('utf-8'))
                    # using io.open lets us dump json as utf-8 so greek letters stay greek
                    with io.open(os.path.join('pass2',tagname), "w", encoding='utf-8') as tagfile:
                        json.dump(tag, tagfile, sort_keys=True, indent=2, ensure_ascii=False)

                except Exception as e:
                    logger.info("Failed to write files for %s - %s" % (fqfn,e))
                    failed += 1

            except Exception as e:
                logger.info("Failed on %s -- %s" % (fqfn,e))
                failed += 1

            filecount += 1


    return (filecount, linecount, failed)

if __name__ == '__main__':
    filecount, linecount, failed = process()
    logger.info("Successfully processed %d files, %d lines" % (filecount, linecount))
    logger.info("Failed on %d files." % (failed))