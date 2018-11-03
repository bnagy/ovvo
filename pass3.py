#!/usr/bin/env python

import json
import sys
import os
import logging
import collatinus
import hashlib
import time
import re
import textwrap
import io

logger = logging.getLogger('root')
FORMAT = "<%(filename)s:%(lineno)3s> in %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

DATE_MAX = 800
poets = ['ovid', 'virgil', 'vergil', 'propertius', 'tibullus', 'catullus', 'persius', 'lucretius']

def acceptable(metadata):
    if metadata['date'] > DATE_MAX:
        return False

    #if any(x in metadata['author'].lower() for x in poets):
    #    return False

    return True

def process():

    filecount = 0
    linecount = 0
    qual_count = 0
    failed = 0
    skipped = 0
    cl = collatinus.comms.Client()
    parser = collatinus.parse.Parser(cl)
    if not os.path.exists('pass3'):
        os.makedirs('pass3')

    for root, dirs, files in os.walk('pass2'):
        dirs[:] = [d for d in dirs if "pass2" in d]
        files[:] = [f for f in files if f.lower().endswith(".txt")]
        for f in files:
            fqfn = os.path.join(root,f)
            testfile = fqfn
            testtag = os.path.splitext(fqfn)[0] + '.json'
            logger.debug("Trying to open %s" % fqfn)
            try:

                try:
                    with open(testtag,'rb') as fh:
                        metadata = json.load(fh)
                    with open(testfile,mode='r', encoding='utf-8') as fh:
                        contents = fh.read()
                except Exception as e:
                    logger.error("Couldn't read files: %s", e)
                    exit(1)


                logger.info("Author -[ %s" % metadata['author'])
                logger.info("Title  -[ %s" % metadata['title'])
                logger.info("Date   -[ %s" % metadata['date'])
                logger.info("%s" % fqfn)
                if not acceptable(metadata):
                    logger.info("[!!] Skipping based on metadata.")
                    skipped += 1
                    continue
                if os.path.isfile(re.sub('pass2', 'pass3', testtag)):
                    logger.info("[!!] Skipping - already have this file.")
                    continue

                try:
                    then = time.time()
                    results = parser.parse(contents)
                    cpu_spent = time.time() - then
                except Exception as e:
                    logger.error("[!!] Failed to parse %s - %s" % (testfile, e))
                    logger.exception(e)
                    exit(1)

                try:
                    if results['sov']+results['svo'] == 0:
                        percent_sov = percent_svo = 0
                    else:
                        percent_sov = results['sov'] / (results['qual'] - results['none'] - results['both'])
                        percent_svo = results['svo'] / (results['qual'] - results['none'] - results['both'])
                    percent_error = (results['none'] + results['both']) / results['qual']
                    percent_qual = results['qual'] / contents.count('\n')
                except:
                    logger.error("[!!] Failed while calculating percentages. Are there qualifying sentences? %s" % results)
                    percent_sov = 0
                    percent_svo = 0
                    percent_error = 100
                    percent_qual = 0

                logger.info("Parsed. %d sentences in %ds, %d qualify. (%d%%)" % 
                    (contents.count('\n'),
                    round(cpu_spent, 2),
                    results['qual'],
                    round(percent_qual*100,2
                    )))
                logger.info("%d SOV %d SVO, %d SKIP, %d AMBIG. [ %.2f SOV, %.2f SVO, %.2f error. ]" % 
                    (results['sov'],
                    results['svo'],
                    results['none'],
                    results['both'],
                    round(percent_sov*100, 2),
                    round(percent_svo*100, 2),
                    round(percent_error*100, 2),
                    ))
                if any(results['sample']):
                    logger.debug("Sample found (%d entries)" % len(results['sample']))

                try:
                    metadata['pass2'] = fqfn
                    new_tag = {**metadata, **results}
                    new_fname = re.sub('pass2', 'pass3', testtag)
                    logger.debug("Writing results...")
                    # using io.open lets us dump json as utf-8 so greek letters stay greek
                    with io.open(new_fname,"w", encoding='utf-8') as tagfile:
                        json.dump(new_tag, tagfile, sort_keys=True, indent=2, ensure_ascii=False)

                except Exception as e:
                    logger.info("Failed to write files for %s - %s" % (fqfn,e))
                    failed += 1

            except Exception as e:
                logger.info("Failed on %s -- %s" % (fqfn,e))
                failed += 1

            filecount += 1
            linecount += results['total']
            qual_count += results['qual']

    return (filecount, linecount, qual_count, failed, skipped)

if __name__ == '__main__':
    filecount, linecount, qual_count, failed, skipped = process()
    logger.info("Successfully processed %d files, %d lines, %d qualifying" % (filecount, linecount, qual_count))
    logger.info("Failed on %d files, skipped %d." % (failed, skipped))