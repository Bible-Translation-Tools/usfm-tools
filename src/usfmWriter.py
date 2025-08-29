# -*- coding: utf-8 -*-
# Implements usfmWriter object to write usfm file with proper spacing.
# By default, all usfm tags except footnotes start on a new line.
# The caller can modify placement of line breaks:
#    by calling setInlineTags() to specify a different set of usfm tags that should not start on a new line
#    by including line breaks in arguments to writeStr()
#    by calling newline() to insert extra line breaks

import io

startline_tags = {'id','ide','usfm','c','cl','v','p','rem',
                'mt','mt1','mt2','mt3','mte','mte1','mte2','ms','ms1','ms2','mr',
                'h','toc1','toc2','toc3',
                'ca','cp',
                'ip','ipi','io','io1','io2','io3','iq','iq1','iq2','iq3','ib',
                'ili','ili1','ili2','ili3','iot','iex','ie',
                'imt','imt1','imt2','im','imi','imq','ipq','is','is1','is2','is3',
                'm','pi','pc','nb','b',
                'q','q1','q2','q3','qa','qr','qc','qm','qm1','qm2',
                's','s1','s2','s3','s4','s5','sr','r','d','sp',
                'sd','sd1','sd2','sd3',
                'esb','esbe','lit','pb','pm','pmo','pmc','pmr'
}
inline_tags = {'va','va*','vp','vp*','ca*',
                'add','add*', 'bd','bd*', 'bdit','bdit*', 'bk','bk*', 'dc','dc*',
                'em','em*', 'it','it*', 'k','k*',
                'nd','nd*', 'no','no*', 'ndx','ndx*', 'ord','ord*',
                'pn','pn*', 'pro','pro*', 'qt','qt*',
                'sc','sc*', 'sig','sig*', 'sls','sls*', 'tl','tl*',
                'w','w*', 'wg','wg*', 'wh','wh*', 'wj','wj*',
                'f','f*','fe','fe*','fr','fk','fq','fqa','fqa*','fp','ft','fv','fv*',
                'fdc','fdc*','fl','fm','fm*','rq','rq*',
                'ef','ef*','ex','ex*','cat','cat*',
                'x','x*','xo','xt',
                'ior','ior*','iqt','iqt*','qac','qac*',
                'fig','fig*'
}

class usfmWriter:
    def __init__(self, path):
        self._path = path
        self._file = io.open(path, "tw", encoding='utf-8', newline='\n')
        self._spaced = True
        self._newlined = True

    def close(self):
        if self._file:
            if not self._newlined:
                self._file.write("\n")
            self._file.close()
            self._file = None

    # Specify a set of usfm tags that do not have to start on a new line
    # See __init__() for the defaults.
    # def setInlineTags(self, tags):
    #     self._inline_tags = tags

    # Writes specified string to the usfm file, inserting spaces where needed.
    # Technical debt: the beginning of the string should be checked for inline tags. Currently
    # this function places all leading usfm markers on a new line.
    def writeStr(self, s):
        if s and self._file:
            if not self._newlined and s[0] == '\\':
                s = "\n" + s
            elif not self._spaced and s[0] not in '.?!;:,)’”»›\n ':
            # Indonesian TBI version of this condition:
            # elif not self._spaced and s[0] not in '.?!;:,)’»›\n ':
                s = " " + s
            self._file.write(s)
            self._spaced = (s[-1] == ' ')
            self._newlined = (s[-1] == '\n')

    # Writes a usfm tagged value, insert newline if needed
    def writeUsfm(self, key, value=None):
        if self._file:
            if key in inline_tags:
                # intro = "\\" if (self._newlined or self._spaced) else " \\"
                intro = '\\'
            else:
                intro = "\\" if self._newlined else "\n\\"
            self._file.write(f"{intro}{key}")
            self._spaced = False
            self._newlined = False
            if value:
                self.writeStr(value)
                if key in {'v', 'ef','ex','f','fe','x'}:
                    self.writeStr(" ")  # ensure correct verse marker even when next char is phrase-ending
                    # ensure space after "\f +" etc.

    # Inserts the specified number of line breaks (defualt 1) into the file.
    def newline(self, n=1):
        if self._file:
            for i in range(n):
                self._file.write("\n")
            self._spaced = True
            self._newlined = True
