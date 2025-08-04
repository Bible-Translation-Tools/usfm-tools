# -*- coding: utf-8 -*-
# Implements usfmReader object to parse usfm files.

import re

all_markers = {'id','ide','usfm','c','cl','v','p','text',   # text is a generated token type
                'add', 'add*', 'bd', 'bd*', 'bdit', 'bdit*', 'bk', 'bk*', 'dc', 'dc*',
                'em', 'em*', 'it', 'it*', 'k', 'k*',
                'nd', 'nd*', 'no', 'no*', 'ndx', 'ndx*', 'ord', 'ord*',
                'pn', 'pn*', 'pro', 'pro*', 'qt', 'qt*',
                'sc', 'sc*', 'sig', 'sig*', 'sls', 'sls*', 'tl', 'tl*',
                'w', 'w*', 'wg', 'wg*', 'wh', 'wh*', 'wj', 'wj*',
                'rq','rq*','f','f*','fe','fe*','fr','fk','fq','fqa','fp','ft','fv','fv*',
                'fdc','fdc*','fl','fm','fm*',
                'x','x*','xo','xt',
                'is','ip','ipi','iot','io','im','imt',
                'm','pi','pc','nb','b','ip','iot','io','io2',
                'q','q1','q2','q3','qa','qr','qc',
                's','s1','s2','s3','s4','s5','sr','r','d','sp',
                'h','toc1','toc2','toc3','mt','mt1',
                'lit','pb','fig','fig*','pmo','pmc','pmr','qm','qm1','qm2'
}

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

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

token_re = re.compile(r'\\([a-z]+[12345*]?)([^\\]*)')
cvnum_re = re.compile(r'\s+([0-9\-+]+)\s+')
footnote_re = re.compile(r'\s+([\-+])\s+')

# Returns a list of USFM Token objects
def parseString(s):
    contents = []
    if not token_re.search(s):
        contents.append(Token('text', s))
    for retoken in re.finditer(token_re, s):
        type = retoken.group(1)
        value = retoken.group(2)
        if type in {'v','c'}:
            if cv := cvnum_re.match(value):
                cvnum = cv.group(1)
                value = value[cv.end():]
            else:
                cvnum = ""
            contents.append(Token(type, cvnum))
            type = 'text'
        elif type == 'f':
            if ff := footnote_re.match(value):
                contents.append(Token(type, ff.group(1)))
                type = None
                value = value[ff.end():]
        elif type.endswith('*'):
            contents.append(Token(type, ''))
            type = 'text' if value.lstrip() else None
        elif type in {'p','pi','pc','nb','m','q','q1','q2','q3','q4','qa','qr','qc',
                      'add','bk','dc','k','lit','nd','ord','pn','qt','sig','sls','tl','wj',
                      'em','bd','it','bdit','no','sc','pb',
                      'fig','ndx','pro','w','wg','wh','fl','fp',
                      'pmo','pmc','pmr','sr','qm','qm1','qm2'}:
            contents.append(Token(type, ''))
            type = 'text'
        valuelines = value.split('\n')
        for line in valuelines:
            value = line.lstrip()
            if value or (type and type != 'text'):
                contents.append(Token(type, value))
            type = 'text'   # any remaining lines are 'text'
    return contents
