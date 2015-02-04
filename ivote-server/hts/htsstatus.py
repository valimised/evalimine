#!/usr/bin/python2.7
# -*- coding: UTF8 -*-

"""
Copyright: Eesti Vabariigi Valimiskomisjon
(Estonian National Electoral Committee), www.vvk.ee
Written in 2004-2014 by Cybernetica AS, www.cyber.ee

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
import htsbase
import formatutil
import zipfile


class StatusCounter:

    def __init__(self):
        self.c_ok = 0
        self.c_bad = 0
        self.c_msg = []

    def ok_c(self):
        return self.c_ok

    def bad_c(self):
        return self.c_bad

    def inc(self, cnt=1, msg=None, res=True):
        if (msg is not None):
            self.c_msg.append(msg)
        if res:
            self.c_ok += cnt
        else:
            self.c_bad += cnt

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

    def valid_vote(self, cnt, msg, res):
        self.v_votes.inc(cnt, msg, res)

    def userrevoked_vote(self, cnt, msg, res):
        self.r_votes.inc(cnt, msg, res)

    def autorevoked_vote(self, cnt, msg, res):
        self.a_votes.inc(cnt, msg, res)

    def unknown_file(self, cnt, msg):
        self.n_votes.inc(cnt, msg)

    def status_output(self, fo):

        fo.write('\nTalletatud hääli %d, korras %d, vigaseid %d\n' %
            (self.v_votes.ok_c() + self.v_votes.bad_c(),
                self.v_votes.ok_c(), self.v_votes.bad_c()))

        fo.write('\nAvalduse alusel tühistatud hääli %d, korras %d, vigaseid %d\n' %
            (self.r_votes.ok_c() + self.r_votes.bad_c(),
                self.r_votes.ok_c(), self.r_votes.bad_c()))

        fo.write('\nTühistatud korduvaid hääli %d, korras %d, vigaseid %d\n' %
            (self.a_votes.ok_c() + self.a_votes.bad_c(),
                self.a_votes.ok_c(), self.a_votes.bad_c()))

        if self.n_votes.ok_c() > 0:
            fo.write('\nVigu olekupuus %d:\n' % self.n_votes.ok_c())
            self.n_votes.print_msg(fo)

        if self.v_votes.c_msg:
            fo.write("\nTalletatud hääled:\n")
            self.v_votes.print_msg(fo)

        if self.r_votes.c_msg:
            fo.write("\nAvalduse alusel tühistatud hääled:\n")
            self.r_votes.print_msg(fo)

        if self.a_votes.c_msg:
            fo.write("\nTühistatud korduvad hääled:\n")
            self.a_votes.print_msg(fo)


class HTSStatus(htsbase.HTSBase):

    def __init__(self, elid):
        htsbase.HTSBase.__init__(self, elid)
        self.__sti = HTSStatusInfo()

    def output(self, outstream):
        outstream.write('Hääletuse \"%s\" olekuanalüüs\n' % self._elid)
        self.__sti.status_output(outstream)

    def do_verify(self, root, vote_file, conf, code):
        res = False
        msg = 'VIGA:\t%s\tTundmatu viga' % code
        inzip = None
        try:
            try:

                lname = root + '/' + vote_file
                inzip = zipfile.ZipFile(lname, 'r')
                bdocdata = inzip.read(htscommon.ZIP_BDOCFILE)

                ver = regrights.analyze_vote(bdocdata, conf)
                if ver.result:
                    res = True
                    msg = 'OK:\t%s\t%s' % (code, ver.ocsp_time)
                else:
                    res = False
                    msg = 'VIGA:\t%s\t%s' % (code, ver.error)
            except Exception as e:
                res = False
                msg = 'Viga:\t%s\t%s' % (code, e)
            except:
                pass
        finally:
            if inzip:
                inzip.close()

        return res, msg

    def status_noverify(self):
        for path in os.walk(self._reg.path(['hts', 'votes'])):
            root = path[0]
            code = root.split('/').pop()

            if not formatutil.is_isikukood(code):
                continue

            user_revoked = False
            vc = 0
            for vote_file in path[2]:
                if htscommon.REVOKE_REASON_PATTERN.match(vote_file):
                    user_revoked = True
                if htscommon.VALID_VOTE_PATTERN.match(vote_file):
                    vc += 1

            if vc > 0:
                if not user_revoked:
                    self.__sti.valid_vote(1, None, True)
                else:
                    self.__sti.userrevoked_vote(1, None, True)
                self.__sti.autorevoked_vote(vc - 1, None, True)

    def status_verify(self):
        import bdocconfig

        tic = ticker.Counter('Hääli:', '\tKorras: %d\tVigaseid: %d')
        tic.start('Hääletuse \"%s\" olekuanalüüs' % self._elid)
        conf = bdocconfig.BDocConfig()
        conf.load(Election().get_bdoc_conf())

        for path in os.walk(self._reg.path(['hts', 'votes'])):
            root = path[0]
            code = root.split('/').pop()

            if not formatutil.is_isikukood(code):
                continue

            user_revoked = False

            valid_files = []
            for vote_file in path[2]:
                if htscommon.REVOKE_REASON_PATTERN.match(vote_file):
                    user_revoked = True
                    continue
                if htscommon.VOTE_VERIFICATION_ID_FILENAME == vote_file:
                    continue
                if htscommon.PARTIAL_VOTE_PATTERN.match(vote_file):
                    continue
                if not htscommon.VALID_VOTE_PATTERN.match(vote_file):
                    self.__sti.unknown_file(1, '\tTundmatu fail: ' + code + '/' + vote_file)
                    continue
                valid_files.append(vote_file)

            if len(valid_files) > 0:
                valid_files.sort()
                latest = valid_files.pop()
                res, msg = self.do_verify(root, latest, conf, code)
                if not user_revoked:
                    self.__sti.valid_vote(1, msg, res)
                else:
                    self.__sti.userrevoked_vote(1, msg, res)
                self.__sti.autorevoked_vote(len(valid_files), None, True)
            else:
                self.__sti.unknown_file(1, '\tHäälteta kaust: ' + code)
                continue

            tic.tick(1 + len(valid_files), self.__sti.ok_count(), self.__sti.bad_count())

        tic.finish(True, self.__sti.ok_count(), self.__sti.bad_count())


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
