import re
import string
import logging
import random
import textwrap

logger = logging.getLogger('root')
FORMAT = "<%(filename)s:%(lineno)3s> in %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

skip_morph = ['infinitive', 'participle', 'gerund', 'passive', 'imperative', 'gerundive']

rgx_letters = re.compile('\w')
rgx_abbrev = re.compile(r'\s[A-Z][a-z]{0,1}\.')
rgx_caps = re.compile(r'\b[A-Z]+\b')
rgx_comma = re.compile('(\w),(\w)')
rgx_space_comma = re.compile('\s+[;,]')

rgx_parens = re.compile('[(<\[].{0,140}?[)>\]]',re.DOTALL)
# these words cause Collatinus to crash. Sex could be the object
# of a transitive verb, but if so then we'll have to live with the error.
rgx_bugwords = re.compile(r'\bcn\b|\bsex\b|\bpost\b|\bpro\b|\bcap\b|\bser\b|\boct\b|\bap\b|\bkal\b|\bti\b|\bst\b|\bpl\b', re.IGNORECASE)

most_punct = string.punctuation.translate({ord(c): None for c in ',;'})
some_punct = string.punctuation.translate({ord(c): None for c in './,;:\'"!?-'})

from cltk.stem.latin.j_v import JVReplacer
jv_replacer = JVReplacer()

from cltk.tokenize.sentence import TokenizeSentence
tokenizer = TokenizeSentence('latin')

class Cleaner(object):

    def general_tidy(self, s):
        s = self.fix_french_quotes(s)
        # remove parenthetical stuff like (Matt. III)
        # or editors stuff like <parvum>
        s = rgx_parens.sub('',s)
        # remove roman numerals
        s = re.sub(r'\b[CXVIMLD]+[\s.,]', '',s)
        # Fix internal spaces in quotes like " currite "
        s = re.compile('" (.{0,500}?) "',re.DOTALL).sub(r'"\1"',s)
        # remove arabic numerals, they're often there as line numbers from OCR
        s = re.sub('\d+','', s)
        # tabs to spaces
        s = re.sub('\t',' ',s)
        # newlines to spaces
        s = re.sub('\n+',' ',s)
        # compress multiple spaces
        s = re.sub('(\s){2,}',' ',s)
        # remove spaces at start of line
        s = re.sub('^\s+', '', s)
        # remove most punctuation.
        s = s.translate({ord(c): None for c in some_punct})
        # spaces before these punctuation marks is probably bogus
        s = re.sub('\s+([.,;?!:])', r'\1', s)
        # remove hyphens that have broken words propera-tum
        s = re.sub('(\S)-(\S)', r'\1\2', s)
        # remove elipses
        s = re.sub(r'\.{2,}', '.', s)
        # normalise end of sentence
        s = re.sub('[?!:]', '.', s)
        # ensure spaces after comma or stop
        s = re.sub('(\w)([.,])(\w)', r'\1\2 \3', s)
        # remaining hyphens can be spaces
        s = re.sub('[-–—]', ' ', s)
        # remove repeated punctuation
        s = re.sub(r'([./,;:\'"!?-])\1+', r'\1', s)
        # things like etc., confuse the parser (stop then comma)
        s = re.sub(r'\.,', ',', s)
        s = re.sub(r',\.', '.', s)
        # remove weird angle braces
        s = re.sub(r'[‹›]', '', s)
        # J-V replacement
        s = jv_replacer.replace(s)

        return s

    def fix_bugs(self, s):
        s = rgx_abbrev.sub('',s)
        s = rgx_caps.sub('',s)
        s = rgx_bugwords.sub('',s)
        # If a bug word got deleted at the start of a line we 
        # might have a stray punctuation mark
        s = re.sub('^\s*[;,]\s*', '', s)
        s = rgx_space_comma.sub(',', s)
        # this weird hypen popped up
        s = re.sub('[-–—]', ' ', s)
        # an OCR artifact in one file
        s = s.replace('€c','')
        # weird unicode dot
        s = s.replace('·',' ')
        # ensure spaces after commas
        s = re.sub('[;,](\w)', r', \1', s) 

        return s

    def fix_french_quotes(self, s):
        s = s.replace('« ','«')
        s = s.replace(' »','»')
        s = s.replace('«','"')
        s = s.replace('»', '"')
        return s

    def wrap(self, s):
        return textwrap.fill(s,100, break_long_words=False, break_on_hyphens=False)

    def tokenize_sentences(self, s):
        s = self.general_tidy(s)
        sents = tokenizer.tokenize_sentences(s)
        clean_sents = []
        for sent in sents:
            # now get rid of almost all punctuation
            s = sent.translate({ord(c): None for c in most_punct})
            # this may need to run multiple times - stripping bugwords
            # can leave more punctuation that needs cleaning etc.
            pre = s
            while True:
                s = self.fix_bugs(pre)
                if s == pre:
                    break
                pre = s
            words = s.split()
            # filter for only words that have at least one \w character in them
            # (filters out punctuation blobs)
            words = list(filter(rgx_letters.search, words))
            # If this sentence is now a fragment, don't bother.
            # Sometimes indices get parsed as single sentences, skip those as well.
            if len(words) < 3 or len(words) > 300:
                continue
            clean_sents.append(' '.join(words))
        return clean_sents
