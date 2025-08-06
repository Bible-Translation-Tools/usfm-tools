# -*- coding: utf-8 -*-
# Implements usfmReader object to parse usfm files.

import re

all_markers = {'id','ide','usfm','c','v','p','rem','text',   # text is a generated token type
                'cl','ca','ca*','cp','va','va*','vp','vp*',
                'add', 'add*', 'bd', 'bd*', 'bdit', 'bdit*', 'bk', 'bk*', 'dc', 'dc*',
                'em', 'em*', 'it', 'it*', 'k', 'k*',
                'nd', 'nd*', 'no', 'no*', 'ndx', 'ndx*', 'ord', 'ord*',
                'pn', 'pn*', 'pro', 'pro*', 'qt', 'qt*',
                'sc', 'sc*', 'sig', 'sig*', 'sls', 'sls*', 'tl', 'tl*',
                'w', 'w*', 'wg', 'wg*', 'wh', 'wh*', 'wj', 'wj*',
                'f','f*','fe','fe*','fr','fk','fq','fqa','fqa*','fp','ft','fv','fv*',
                'fdc','fdc*','fl','fm','fm*','rq','rq*',
                'x','x*','xo','xt',
                'imt','imt1','imt2','im','imi','imq','ipq','is','is1','is2','is3',
                'ip','ipi','io','io1','io2','io3','iq','iq1','iq2','iq3','ib',
                'ili','ili1','ili2','ili3','iot','iex',
                'ior','ior*','iqt','iqt*','ie',
                'm','pi','pc','nb','b','ip','iot','io','io2',
                'q','q1','q2','q3','qa','qr','qc',
                's','s1','s2','s3','s4','s5','sr','r','d','sp',
                'sd','sd1','sd2','sd3',
                'h','toc1','toc2','toc3',
                'mt','mt1','mt2','mt3','mte','mte1','mte2','ms','ms1','ms2','mr',
                'lit','pb','fig','fig*','pmo','pmc','pmr','qm','qm1','qm2'
}

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f'Token({self.type}, {self.value})'

    def isCharacterStyle(self):
        return self.type in {'add', 'add*', 'bd', 'bd*', 'bdit', 'bdit*', 'bk', 'bk*', 'dc', 'dc*',
                    'em', 'em*', 'it', 'it*', 'k', 'k*',
                    'nd', 'nd*', 'no', 'no*', 'ndx', 'ndx*', 'ord', 'ord*',
                    'pn', 'pn*', 'pro', 'pro*', 'qt', 'qt*',
                    'sc', 'sc*', 'sig', 'sig*', 'sls', 'sls*', 'tl', 'tl*',
                    'w', 'w*', 'wg', 'wg*', 'wh', 'wh*', 'wj', 'wj*'}
    def isCrossRef(self):
        return self.type in {'x','x*','xo','xt'}
    # Returns true if token is part of a footnote
    def isFootnote(self):
        return self.type in {'rq','rq*','f','f*','fe','fe*','fr','fk','fq','fqa','fp','ft','fv','fv*',
                             'fdc','fdc*','fl','fm','fm*'}
    def isIntro(self):
        return self.type in {'is','ip','ipi','iot','io','im','imt','imt1'}
    def isParagraph(self):
        return self.type in {'p','m','pi','pc','nb','b','ip','iot','io','io2'}
    def isPoetry(self):
        return self.type in {'q','q1','q2','q3','qa','qr','qc'}
    def isSection(self):
        return self.type in {'s','s1','s2','s3','s4','s5','sr','r','d','sp'}
    def isSpecialText(self):
        return self.type in {'wj','add','nd','pn','qt','k'}
    def isTitleToken(self):
        return self.type in {'h','toc1','toc2','toc3','mt','mt1','imt','imt1'}

token_re = re.compile(r'\\([a-z]+[12345\*]?)([^\\]*)')

# Returns the first re match object in the string which is valid usfm.
def find_usfm(s, pos):
    obj = None
    obj = token_re.search(s, pos)
    while obj and obj.group(1) not in all_markers:
        obj = token_re.search(s, obj.end()-1)
    return obj

# Iterator: returns Tokens of ['text', value] or [usfm-tag, value]
# The value part of the Token includes everything up to the next valid usfm-tag.
def nextpair(text):
    for s in text.split('\n'):
        while s:
            token = find_usfm(s, 0)
            if not token:
                yield Token('text', s.strip())
                break
            else:
                if token.start() > 0:
                    yield Token('text', s[0:token.start()].strip())
                nexttoken = find_usfm(s, token.end())
                if nexttoken:
                    yield Token(token.group(1), token.group(2).strip())
                    s = s[nexttoken.start():]
                else:
                    yield Token(token.group(1), s[token.start(2):].strip())
                    s = s[token.end():].lstrip()
                    if s.startswith('\\'):  # backslash without a next token
                        break

cnum_re = re.compile(r'([0-9]+)')
vnum_re = re.compile(r'([0-9\-]+)\s*')
footnote_re = re.compile(r'\s+([\-+])\s+')

def parseString(s):
    contents = []
    for pair in nextpair(s):
        leftover = ""
        if pair.type == 'c':
            if cc := cnum_re.match(pair.value):
                contents.append(Token(pair.type, cc.group(1)))
                leftover = pair.value[cc.end():]
            else:
                contents.append(Token(pair.type, ""))
                leftover = pair.value
        elif pair.type == 'v':
            if vv := vnum_re.match(pair.value):
                contents.append( Token(pair.type, vv.group(1)) )
                leftover = pair.value[vv.end():]
            else:
                contents.append(Token(pair.type, ""))
                leftover = pair.value
        elif type == 'f':
            if ff := footnote_re.match(pair.value):
                contents.append(Token(pair.type, ff.group(1)))
                leftover = pair.value[ff.end():]
        elif pair.type.endswith('*'):
            contents.append(Token(pair.type, ''))
            leftover = pair.value
        elif pair.type in {'p','pi','pc','nb','m','q','q1','q2','q3','q4','qa','qr','qc',
                      'add','bk','dc','k','lit','nd','ord','pn','qt','sig','sls','tl','wj',
                      'em','bd','it','bdit','no','sc','pb',
                      'fig','ndx','pro','w','wg','wh','fl','fp',
                      'pmo','pmc','pmr','sr','qm','qm1','qm2'}:
            contents.append(Token(pair.type, ''))
            leftover = pair.value
        else:
            contents.append(Token(pair.type, pair.value))
        if leftover:
            contents.append( Token('text', leftover) )
    return contents
