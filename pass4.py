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
import csv

logger = logging.getLogger('root')
FORMAT = "<%(filename)s:%(lineno)3s> in %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)
cleaner = collatinus.clean.Cleaner()

def process():
    filecount = 0
    linecount = 0
    qualcount = 0
    failed = 0
    with open('pass4.csv', 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['author', 'title', 'date', 'lines', 'qual', 'ov', 'vo', 'none', 'both']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for root, dirs, files in os.walk('pass3'):
            files[:] = [f for f in files if f.lower().endswith(".json")]
            for f in files:
                fqfn = os.path.join(root,f)
                try:
                    basename = os.path.splitext(f)[0]
                    fqtagname = os.path.join(root, "%s.json" % basename)
                    with open(fqtagname) as th:
                        tag = json.load(th)
                    logger.info("[file]   %s" % fqfn)
                    logger.info("[work]   %s -- %s" % (tag['author'], tag['title']))
                    filecount += 1
                    linecount += tag['lines']
                    qualcount += tag['qual']
                    tag['author'] = tag['author'].rstrip(' ')
                    writer.writerow(tag)
                except Exception as e:
                    logger.error("Error: %s" % e)
                    failed += 1 

    return (filecount, linecount, qualcount, failed)

def main():
    filecount, linecount, qualcount, failed = process()
    logger.info("Successfully processed %d files, %d lines, %d qualify" % (filecount, linecount, qualcount))
    logger.info("Failed on %d files." % (failed))

if __name__ == '__main__':
    main()