import logging
import os
import re
import hashlib
import random
import io
import json
from bs4 import BeautifulSoup

logger = logging.getLogger('root')
FORMAT = "<%(filename)s:%(lineno)3s> in %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

class Preprocessor(object):

    def process(self, fqfn, outdir):

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        with open(fqfn) as fh:
            # Parse using BeautifulSoup
            try:
                soup = BeautifulSoup(fh,"xml")
            except Exception as e:
                raise Exception("Failed to parse XML: %s" % e)

            try:
                author = self._get_author(soup)
            except Exception as e:
                raise Exception("Failed to get author for %s - %s" % (fqfn,e))

            try:
                date = self._get_date(soup)
            except Exception as e:
                raise Exception("Failed to get date for %s - %s" % (fqfn,e))
            if not date:
                raise Exception("No date.")
            try:
                title = self._get_title(soup)
            except Exception as e:
                raise Exception("Failed to get title for %s - %s" % (fqfn,e))

            try:
                text = self._get_text(soup)
                if text:
                    lines = text.count('\n')
            except Exception as e:
                raise Exception("Failed to get text for %s - %s" % (fqfn,e))
            if not text:
                raise Exception("No text.")

            tag = {
                'file' : fqfn,
                'author' : author,
                'date' : date,
                'lines' : lines,
                'title' : title
            }
            h = hashlib.sha256(text.encode('utf-8'))
            hex_dig = h.hexdigest()
            logger.info("[file]   %s" % fqfn)
            logger.info("[shasum] %s" % hex_dig)
            logger.info("[author] %s" % author)
            logger.info("[title]  %s" % title)
            logger.info("[date]   %s" % date)
            logger.info("[lines]  %s" % lines)

            try:
                fname = "%s.txt" % hex_dig
                tagname = "%s.json" % hex_dig
                with open(os.path.join(outdir,fname),"wb") as f:
                    f.write(text.encode('utf-8'))
                with io.open(os.path.join(outdir,tagname), "w", encoding='utf-8') as tagfile:
                    json.dump(tag, tagfile, sort_keys=True, indent=2, ensure_ascii=False)

            except Exception as e:
                raise Exception("Failed to write files for %s - %s" % (fqfn,e))
            return tag
                
    def _parse_date(self, ds):

        # Generally we only have the author's dates, so we
        # take the midpoint between when they were 18 and
        # when they died.

        # print(" ".join("{:02x}".format(ord(c)) for c in ds))
        # Two different unicode dashes are sometimes used
        ds = ds.replace('\u2013', '-')
        ds = ds.replace('\u2014', '-')
        ds = ds.replace("c.", '')
        ds = ds.replace("fl.",'')
        # filter empty strings, list() turns a Py3 iterator back into a list
        arr = list(filter(None,ds.split("-",2)))
        res = []
        for x in arr:
            # kill punctuation now
            x = re.sub(r'[^\w\s]','',x)
            if "BC" in x.upper():
                res.append( -int(re.sub(r'BC','',x,flags=re.IGNORECASE)) )
            else:
                res.append( int(x) )
        # python does banker's rounding (rounds to even on .5)    
        if len(res) == 2:
            return round(random.uniform(res[0]+18, res[1]),2)
        else:
            return res[0]

    def _get_author(self, soup):
        author = ""
        if soup.select("teiHeader > author"):
            for tag in soup.select("teiHeader > author"):
                if tag.name == "date":
                    continue
                author += tag.string 
        else:
            if soup.find("author"):
                for tag in soup.find("author").contents:
                    if tag.name == "date": 
                        continue
                    author += tag.string 
                   
        return author

    def _get_date(self, soup):
        date = None
        # Sometimes the title has a date for the actual work
        if soup.select("title > date"):
            date = soup.select("title > date")[0].string
        else:
           # otherwise make do with the author's dates
            if soup.select("author > date"):
                date = soup.select("author > date")[0].string
        if date:
            try:
                return self._parse_date(date)
            except Exception as e:
                logger.debug(e)
                return None

        return None

    def _get_title(self, soup):
        title = ""
        if soup.find("bibl") and soup.bibl.find("title"):
            # Some titles contain empty </s> tags we want to ignore
            # but some also contain a <date> which should not
            # be included
            for tag in soup.bibl.title.contents:
                if tag.name != "date" and tag.string:
                    title += tag.string
        else:
            if soup.find("title"):
                for tag in soup.title.contents:
                    if tag.name != "date" and tag.string:
                        title += tag.string
        return title

    def _get_text(self, soup):
        text = None
        if soup.find("text"):
            text = soup.find("text").get_text()
        else:
            # A very few of the Perseus files use <body> tags instead of <text>
            if soup.find("body"):
                text = soup.find("body").get_text()
        return text