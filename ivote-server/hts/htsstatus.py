#!/usr/bin/python2.7
# -*- coding: UTF8 -*-

"""
Copyright: Eesti Vabariigi Valimiskomisjon
(Estonian National Electoral Committee), www.vvk.ee
Written in 2004-2013 by Cybernetica AS, www.cyber.ee

This work is licensed under the Creative Commons
Attribution-NonCommercial-NoDerivs 3.0 Unported License.
To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc-nd/3.0/.
"""

from election import Election
import regrights
import ticker
import os
import htscommon


class StatusCounter:

    def __init__(self):
        self.c_ok = 0
        self.c_bad = 0
        self.c_msg = []

    def ok_c(self):
        return self.c_ok

    def bad_c(self):
        return self.c_bad

    def inc(self, msg=None, res=True):
        if (msg != None):
            self.c_msg.append(msg)
        if res:
            self.c_ok += 1
        else:
            self.c_bad += 1

    def print_msg(self, fo):
        for el in self.c_msg:
            fo.write('\t%s\n' % el)


class HTSStatusInfo:

    def __init__(self):
        self.v_votes = StatusCounter()
        self.a_votes = StatusCounter()
        self.r_votes = StatusCounter()
        self.n_votes = StatusCounter()

    def ok_count(self):
        return self.v_votes.ok_c() + self.a_votes.ok_c() + self.r_votes.ok_c()

    def bad_count(self):
        return \
            self.v_votes.bad_c() + self.a_votes.bad_c() + self.r_votes.bad_c()

    def valid_vote(self, msg, res):
        self.v_votes.inc(msg, res)

    def userrevoked_vote(self, msg, res):
        self.r_votes.inc(msg, res)

    def autorevoked_vote(self, msg, res):
        self.a_votes.inc(msg, res)

    def unknown_file(self, msg):
        self.n_votes.inc(msg)

    def status_output(self, fo):

        fo.write('\nTalletatud hääli %d:\n' % \
            (self.v_votes.ok_c() + self.v_votes.bad_c()))
        self.v_votes.print_msg(fo)
        fo.write('\tKorras hääli (%d), vigaseid hääli (%d)\n' % \
            (self.v_votes.ok_c(), self.v_votes.bad_c()))

        fo.write('\nAvalduse alusel tühistatud hääli %d:\n' % \
            (self.r_votes.ok_c() + self.r_votes.bad_c()))
        self.r_votes.print_msg(fo)
        fo.write('\tKorras hääli (%d), vigaseid hääli (%d)\n' % \
            (self.r_votes.ok_c(), self.r_votes.bad_c()))

        fo.write('\nTühistatud korduvaid hääli %d:\n' % \
            (self.a_votes.ok_c() + self.a_votes.bad_c()))
        self.a_votes.print_msg(fo)
        fo.write('\tKorras hääli (%d), vigaseid hääli (%d)\n' % \
            (self.a_votes.ok_c(), self.a_votes.bad_c()))

        if self.n_votes.ok_c() > 0:
            fo.write('\nVigu olekupuus %d:\n' % self.n_votes.ok_c())
            self.n_votes.print_msg(fo)


class HTSStatus:

    def __init__(self, elid):
        self.__reg = Election().get_sub_reg(elid)
        self.__elid = elid
        self.__sti = HTSStatusInfo()

    def output(self, outstream):
        outstream.write('Hääletuse \"%s\" olekuanalüüs\n' % self.__elid)
        self.__sti.status_output(outstream)

    def do_verify(self, root, vote_file, conf, code):
        res = False
        msg = 'VIGA:\t%s\tTundmatu viga' % code
        try:
            ver = regrights.analyze_vote(root + '/' + vote_file, conf)
            if ver.result:
                res = True
                msg = 'OK:\t%s\t%s' % (code, ver.ocsp_time)
            else:
                res = False
                msg = 'VIGA:\t%s\t%s' % (code, ver.error)
        except Exception, e:
            res = False
            msg = 'Viga:\t%s\t%s' % (code, e)
        except:
            pass

        return res, msg

    def calculate(self, verify):
        import bdocpythonutils
        tic = ticker.Counter('Hääli:', '\tKorras: %d\tVigaseid: %d')
        tic.start('Hääletuse \"%s\" olekuanalüüs' % self.__elid)
        conf = bdocpythonutils.BDocConfig()
        conf.load(Election().get_bdoc_conf())
        for path in os.walk(self.__reg.path(['hts', 'votes'])):
            root = path[0]
            for vote_file in path[2]:
                code = root.split('/').pop()
                msg = None
                res = True
                if verify:
                    res, msg = self.do_verify(root, vote_file, conf, code)

                if htscommon.VALID_VOTE_PATTERN.match(vote_file):
                    self.__sti.valid_vote(msg, res)
                elif htscommon.USERREVOKED_VOTE_PATTERN.match(vote_file):
                    self.__sti.userrevoked_vote(msg, res)
                elif htscommon.AUTOREVOKED_VOTE_PATTERN.match(vote_file):
                    self.__sti.autorevoked_vote(msg, res)
                elif htscommon.REVOKE_REASON_PATTERN.match(vote_file):
                    pass
                elif htscommon.VOTE_VERIFICATION_ID_FILENAME == vote_file:
                    pass
                else:
                    self.__sti.unknown_file('\t' + root + '/' + vote_file)

                tic.tick(1, self.__sti.ok_count(), self.__sti.bad_count())

        tic.finish()


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
