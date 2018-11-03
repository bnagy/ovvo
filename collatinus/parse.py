import re
import string
import logging
import random
import textwrap
from . import clean

logger = logging.getLogger('root')
FORMAT = "<%(filename)s:%(lineno)3s> in %(funcName)s ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

qualifying_verbs = ['accedo', 'accipio', 'addo', 'advenio', 'adverto', 'affero', 'afficio',
'agito', 'alo', 'amitto', 'amo', 'aperio', 'appello', 'aspicio', 'audio',
'aufero', 'caedo', 'capio', 'cingo', 'claudo', 'cogo', 'colligo', 'colo', 'committo',
'comparo', 'compono', 'condo', 'confero', 'conficio', 'consequor', 'constituo', 'consulo',
'consumo', 'contemno', 'contineo', 'contingo', 'convenio', 'corrumpo', 'credo',
'creo', 'cupio', 'curo', 'damno', 'deduco', 'defendo', 'defero', 'desero', 'desidero',
'desum', 'diligo', 'dimitto', 'disco', 'divido', 'do', 'doceo', 'dono',
'duco', 'educo', 'effundo', 'eligo', 'eripio', 'excipio', 'exigo', 'experior',
'exspecto', 'fallo', 'fero', 'fingo', 'frango', 'fruor', 'fugo', 'fundo', 'gero',
'gigno', 'habeo', 'hortor', 'iacio', 'impero', 'impleo', 'impono', 'incido', 'indico',
'instituo', 'intellego', 'intendo', 'interficio', 'interrogo', 'intro', 'invenio',
'iungo', 'iuvo', 'laedo', 'laudo', 'lego', 'malo', 'memini', 'mereo', 'metuo',
'miror', 'misceo', 'mitto', 'nescio', 'noceo', 'nolo', 'occido', 'occupo',
'occurro', 'odi', 'offero', 'opto', 'ostendo', 'parco', 'pareo', 'pario', 'paro',
'patior', 'pello', 'pendo', 'perdo', 'permitto', 'pertineo', 'pervenio', 'peto',
'placeo', 'pono', 'posco', 'praebeo', 'premo', 'probo', 'prodo', 'prohibeo', 'promitto',
'pugno', 'rapio', 'recipio', 'reddo', 'relinquo', 'respicio', 'retineo', 'revoco',
'rideo', 'rumpo', 'scio', 'scribo', 'sentio', 'sequor', 'servo', 'spargo', 'specto',
'subeo', 'sumo', 'supero', 'suscipio', 'sustineo', 'tango', 'tego', 'tempto', 'teneo',
'terreo', 'timeo', 'tollo', 'trado', 'traho', 'transeo', 'turbo', 'veho', 'vereor',
'video', 'vinco', 'vito', 'voco']

skip_morph = ['infinitive', 'participle', 'gerund', 'passive', 'imperative', 'gerundive']

rgx_letters = re.compile('\w')
rgx_caps = re.compile(r'\b[A-Z]+\b')
rgx_comma = re.compile('(\w),(\w)')
rgx_space_comma = re.compile('\s+,')
# these words cause Collatinus to crash. Sex could be the object
# of a transitive verb, but if so then we'll have to live with the error.
rgx_bugs = re.compile('cn|sex|post|pro|cap|ser|oct|ap', re.IGNORECASE)
most_punct = string.punctuation.translate({ord(c): None for c in ',;'})
rgx_bugwords = re.compile(r'\bcn\b|\bsex\b|\bpost\b|\bpro\b|\bcap\b|\bser\b|\boct\b|\bap\b', re.IGNORECASE)

cleaner = clean.Cleaner()

class Parser(object):
    def __init__(self, client, sample_pct=1):
        self._client = client
        self._sample_pct = sample_pct

    def _decorate(self, w):
        # Analyse a word, return a tuple (IsKnown, PossiblyAccusative)
        for tag in self._client.tag(w):
            if len(tag) < 10: #unknown
                return((False, False))
            if 'accusative' in tag[9]:
                return((True,True))
        return ((True,False))

    def _punctuated(self, s):
        return s.endswith(',') or s.endswith(';') or s.endswith('.')

    def parse(self, contents):

        ''' 
        Parse a set of sentences, one per line, using Collatinus
        '''
        
        sents = contents.split('\n')
        logger.debug(" PARSING: %d sentences to do" % len(sents))
        sent_count = len(sents)
        qualify_count = 0
        sov_count, svo_count, none_count, both_count = 0,0,0,0
        sample = []

        # TAG FORMAT
        # 0[ '1', - global index
        # 1 '1', - phrase index
        # 2 '1', - index in phrase
        # 3 'Liber', - word parsed
        # 4 'n11', - morphology code
        # 5 'liber', - lemma
        # 6 'liber, bri, m.', - conjugation
        # 7 '300', - LASLA frequency??
        # 8 'book, volume; inner bark of a tree', - definition
        # 9 'liber nominative singular' - parse
        # ]
        for sent in sents:

            # Remove words that make Collatinus bug out.
            logger.debug("Pre-Bugfix: %s" % sent)
            pre = sent
            while True:
                sent = cleaner.fix_bugs(pre)
                if sent == pre:
                    break
                pre = sent
            logger.debug("Post-Bugfix: %s" % sent)
            words = sent.split()

            tagged = self._client.tag_best(sent)
            # unknown if the tag is too short
            unknown = list(filter(lambda x: len(x) < 10, tagged))
            if len(unknown)/len(words) >= 1/3:
                # too many unknown words - possibly not even in Latin.
                logger.debug("[!!] Skip. Too many unknowns ( %d out of %d)" % (len(unknown), len(words)))
                continue

            for tag in tagged:
                if len(tag) < 4:
                    # If Collatinus crashes client.py sends back an empty list. A
                    # failure to parse won't trigger here, since it will have at
                    # least eg [1,1,1,someword,'unknown'] T
                    # These hard errors tend not to be recoverable.
                    logger.error(" HARD ERROR (server has crashed!) - Aborting.")
                    exit(1)

                if 'unknown' in tag[3]:
                    continue

                if tag[5] in qualifying_verbs:

                    if any(x in tag[9] for x in skip_morph):
                        # skip non-qualifying forms of qualifying qualifying_verbs
                        continue
                    try:
                        logger.debug(tag[9])
                        # just the first two definitions, it's only a reminder for human reviewers.
                        vrb_debug = "VERB: %s - %s" % (tag[5],';'.join(tag[8].split(';')[:2]))
                        logger.debug(vrb_debug)
                    except:
                        logger.debug(tag) # unknown tags are only length 4

                    qualify_count += 1
                    sent_dbg = "SENTENCE: %s" % sent.replace(tag[3], '<<%s>>' % tag[3])
                    logger.debug(sent_dbg)
                    pos = int(tag[0]) - 1

                    if tag[3] not in words[pos]:
                        # some kind of indexing mismatch, severe internal bug
                        logger.error(" Indexing error - verb not in expected position.")
                        logger.error(sent_dbg)
                        logger.error(words[pos])
                        logger.error(tag)
                        exit(1)

                    result = ['<<%s>>' % words[pos]]
                    acc_before, acc_after = False, False
                    if pos > 0:
                        # look backwards up to three words (unless start of sentence)
                        for i in range(pos-1,pos-4,-1):
                            if i < 0: break
                            if self._punctuated(words[i]): break
                            known, acc = self._decorate(words[i])
                            if acc:
                                result.insert(0,'[%s]' % words[i])
                                acc_before = True
                                break
                            elif not known:
                                result.insert(0,'{%s}' % words[i])
                            else:
                                result.insert(0, words[i])
                    if pos < len(words) and not self._punctuated(words[pos]):
                        # look forwards unless end of sentence or verb is punctated
                        for i in range(pos+1, pos+4, 1):
                            if i >= len(words): break
                            known, acc = self._decorate(words[i])
                            if acc:
                                result.append('[%s]' % words[i])
                                acc_after = True
                                break
                            elif not known:
                                result.append('{%s}' % words[i])
                            else:
                                result.append(words[i])
                            if self._punctuated(words[i]): break


                    logger.debug(" SLICE: %s" % result)
                    if acc_before and not acc_after:
                        logger.debug(" RESULT: OV")
                        sov_count += 1
                        if random.random() <= (self._sample_pct/100.0):
                            sample.append(
                                [
                                vrb_debug,
                                textwrap.fill(sent_dbg,100, break_long_words=False, break_on_hyphens=False),
                                result,
                                "RESULT: OV"
                                ])
                    elif acc_after and not acc_before:
                        logger.debug(" RESULT: VO")
                        svo_count += 1
                        if random.random() <= (self._sample_pct/100.0):
                            sample.append(
                                [
                                vrb_debug,
                                textwrap.fill(sent_dbg,100, break_long_words=False, break_on_hyphens=False),
                                result,
                                "RESULT: VO"
                                ])
                    elif not acc_after and not acc_before:
                        logger.debug(" RESULT: NONE")
                        none_count += 1
                    else:
                        logger.debug(" RESULT: BOTH")
                        both_count += 1



        return(
            {
                'sov': sov_count,
                'svo': svo_count,
                'none': none_count,
                'both': both_count,
                'qual': qualify_count,
                'total': sent_count,
                'sample': sample
            })
