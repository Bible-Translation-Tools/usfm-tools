# -*- coding: utf-8 -*-
# Implements usfmReader object to parse usfm files.

import re

all_markers = {'id','ide','usfm','c','v','p','rem','text',   # text is an internally generated token type, not a marker
                'cl','ca','ca*','cp','va','va*','vp','vp*',
                'add','+add','add*','+ad*', 'bd','+bd','bd*','+bd*', 'bdit','+bdit','bdit*','+bdit*',
                'bk','+bk','bk*','+bk*', 'dc','+dc','dc*','+dc*',
                'em','+em','em*','+em*', 'it','+it','it*','+it*', 'k','+k','k*','+k*',
                'nd','+nd','nd*','+nd*', 'no','+no','no*','+no*', 'ndx','+ndx','ndx*','+ndx*', 'ord','+ord','ord*','+ord*',
                'pn','+pn','pn*','+pn*', 'pro','+pro','pro*','+pro*', 'qt','+qt','qt*','+qt*',
                'sc','+sc','sc*','+sc*', 'sup', '+sup','sup*','+sup*',
                'sig','+sig','sig*','+sig*', 'sls','+sls','sls*','+sls*', 'tl','+tl','tl*','+tl*',
                'w','+w','w*','+w*', 'wg','+wg','wg*','+wg*', 'wh','+wh','wh*','+wh*', 'wj','+wj','wj*','+wj*',
                'f','f*','fe','fe*','fr','fk','fl','fq','fqa','fp','ft',
                'fv','+fv','fv*','+fv*','fdc','+fdc','fdc*','+fdc*', 'fm','+fm','fm*','+fm*',
                'rq','+rq','rq*','+rq*',
                'x','x*','xo','xt','ef','ef*','ex','ex*','cat','cat*','esb','esbe',
                'imt','imt1','imt2','im','imi','imq','ipq','is','is1','is2','is3',
                'ip','ipi','io','io1','io2','io3','iq','iq1','iq2','iq3','ib',
                'ili','ili1','ili2','ili3','iot','iex',
                'ior','+ior','ior*','+ior*', 'iqt','iqt*','ie',
                'm','pi','pi1','pi2','pi3','pc','nb','b',
                'q','q1','q2','q3','qa','qr','qc','qac','qac*','qs','qs*','qm','qm1','qm2',
                's','s1','s2','s3','s4','s5','sr','r','d','sp',
                'sd','sd1','sd2','sd3',
                'h','toc1','toc2','toc3',
                'mt','mt1','mt2','mt3','mte','mte1','mte2','ms','ms1','ms2','mr',
                'lit','pb','fig','fig*','pm','pmo','pmc','pmr'
}

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f'Token({self.type}, {self.value})'

    def isCharacterStyle(self):
        return self.type in {'add','+add','add*','+ad*', 'bd','+bd','bd*','+bd*', 'bdit','+bdit','bdit*','+bdit*',
            'bk','+bk','bk*','+bk*', 'dc','+dc','dc*','+dc*',
            'em','+en','em*','+em*', 'it','+it','it*','+it*', 'k','+k','k*','+k*',
            'nd','+nd','nd*','+nd*', 'no','+no','no*','+no*', 'ndx','+ndx','ndx*','+ndx*', 'ord','+ord','ord*','+ord*',
            'pn','+pn','pn*','+pn*', 'pro','+pro','pro*','+pro*', 'qt','+qt','qt*','+qt*',
            'sc','+sc','sc*','+sc*', 'sig','+sig','sig*','+sig*', 'sls','+sls','sls*','+sls*', 'tl','+tl','tl*','+tl*',
            'sup', '+sup','sup*','+sup*',
            'w','+w','w*','+w*', 'wg','+wg','wg*','+wg*', 'wh','+wh','wh*','+wh*', 'wj','+wj','wj*','+wj*'
        }

    def isCrossRef(self):
        return self.type in {'x','x*','xo','xt'}
    # Returns true if token is part of a footnote
    def isFootnote(self):
        return self.type in {'f','f*','fe','fe*','ex','ex*','ef','ef*',
            'fr','fk','fl','fq','fqa','fp','ft',
            'fv','+fv','fv*','+fv*','fdc','+fdc','fdc*','+fdc*', 'fm','+fm','fm*','+fm*',
            'rq','+rq','rq*','+rq*'
        }
    def isFootnoteInterior(self):
        return self.type in {'fr','fk','fl','fq','fqa','fp','ft',
            'fv','+fv','fv*','+fv*','fdc','+fdc','fdc*','+fdc*', 'fm','+fm','fm*','+fm*',
            'rq','+rq','rq*','+rq*'
        }
    def isIntro(self):
        return self.type in {'is','ip','ipi','iot','io','im','imt','imt1'}
    def isParagraph(self):
        return self.type in {'p','m','pi','pi1','pi2','pi3','pc','nb','b','ip','iot','io','io2'}
    def isPoetry(self):
        return self.type in {'q','q1','q2','q3','qa','qr','qc','qm','qm1','qm2','qs','qac'}
    def isSection(self):
        return self.type in {'s','s1','s2','s3','s4','s5','sr','r','d','sp'}
    def isSpecialText(self):
        return self.type in {'wj','add','nd','pn','qt','k'}
    def isTitleToken(self):
        return self.type in {'h','toc1','toc2','toc3','mt','mt1','imt','imt1'}

# For internal use
# A Pair is like a Token but the value part has not been stripped of spaces.
class Pair:
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __repr__(self):
        return f'Pair({self.type}, {self.value})'

token_re = re.compile(r'\\(\+?[a-z]+[12345\*]?)([^\\]*)')

# Returns the list of (tag, pos) in the string
#   tag is a valid usfm marker, minus the backslash
#   pos is the position of the backslash in the string
def list_usfm(s):
    usfms = []
    obj = token_re.search(s)
    while obj:
        while obj and not obj.group(1) in all_markers:
            obj = token_re.search(s, obj.end(1))
        if obj:
            usfms.append((obj.group(1), obj.start()))
            obj = token_re.search(s, obj.end(1))
    return usfms

# Iterator: returns Pairs of ['text', value] or [usfm-tag, value]
# The value part of the Pair includes everything up to the next valid usfm-tag or newline,
# wehther or not it belong with usfm-tag
# Does not strip space characters!
def nextpair(text):
    for line in text.split('\n'):
        usfms = list_usfm(line)
        if not usfms:
            if line:
                yield(Pair('text', line))
        else:
            usfm = usfms[0]
            if usfm[1] > 0:
                yield(Pair('text', line[0:usfm[1]]))
            for i in range(1,len(usfms)):
                # assert usfm
                nextusfm = usfms[i]
                startpos = usfm[1] + len(usfm[0]) + 1
                yield(Pair(usfm[0], line[startpos:nextusfm[1]]))
                usfm = nextusfm
            if usfm:
                startpos = usfm[1] + len(usfm[0]) + 1
                yield(Pair(usfm[0], line[startpos:]))

cnum_re = re.compile(r'\s+([0-9]+)')
# vnum_re = re.compile(r'\s+([0-9\-]+)\s*')
vnum_re = re.compile(r'\s+([0-9\-]+)( +|\\|$)')
plus_re = re.compile(r'\s+([\-+])\s+')


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
        elif pair.type in {'f','fe','x'}:
            if plus := plus_re.match(pair.value):
                contents.append(Token(pair.type, plus.group(1)))
                leftover = pair.value[plus.end():]
        elif pair.type.endswith('*'):
            contents.append(Token(pair.type, ''))
            leftover = pair.value
        elif pair.type in {'p','pi','pi1','pi2','pi3','pc','nb','m','q','q1','q2','q3','q4','qa','qr','qc',
                      'add','bk','dc','k','lit','nd','ord','pn','qt','sig','sls','tl','wj',
                      'em','bd','it','bdit','no','sc','pb',
                      'fig','ndx','pro','w','wg','wh','fl','fp',
                      'pm','pmo','pmc','pmr','sr','qm','qm1','qm2'}:
            contents.append(Token(pair.type, ''))
            leftover = pair.value
        else:
            contents.append(Token(pair.type, pair.value.lstrip()))
        if leftover.lstrip():
            contents.append( Token('text', leftover.lstrip()) )
    return contents
