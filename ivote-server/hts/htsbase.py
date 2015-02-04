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

import evlog
import htscommon
import evcommon
from election import Election
import os
import inputlists
import bdocpythonutils
import zipfile
import time


def get_vote(zipfn):
    bdoc = None
    inzip = None
    try:
        try:
            inzip = zipfile.ZipFile(zipfn, 'r')
            bdocdata = inzip.read(htscommon.ZIP_BDOCFILE)
            bdoc = bdocpythonutils.BDocContainer()
            bdoc.load_bytes(bdocdata)
            profile = bdocpythonutils.ManifestProfile('TM')
            bdoc.validate(profile)
        except:
            bdoc = None
            evlog.log_exception()
    finally:
        if inzip:
            inzip.close()

    return bdoc


class HTSBase:

    def __init__(self, elid):
        self._elid = elid
        self._errmsg = None
        self._reg = Election().get_sub_reg(self._elid)

        self._revlog = evlog.Logger()
        self._revlog.set_format(evlog.RevLogFormat())
        self._revlog.set_logs(self._reg.path(['common', evcommon.REVLOG_FILE]))

    def haaletanud(self, isikukood):
        latest = self.get_latest_vote(isikukood)
        return latest is not None

    def get_revoked_path(self, pc):
        user_key = htscommon.get_user_key(pc)
        return self._reg.path(user_key + ['reason'])

    def get_latest_vote(self, pc):
        user_key = htscommon.get_user_key(pc)
        if self._reg.check(user_key):
            files = self._reg.list_keys(user_key)
            votes = []
            for el in files:
                if htscommon.VALID_VOTE_PATTERN.match(el):
                    votes.append(el)
            votes.sort()
            latest = votes.pop()
            if latest:
                return htscommon.get_votefile_time(latest)

        return None

    def restore_vote(self, revline, operator):
        timest = self.get_latest_vote(revline[0])
        os.unlink(self.get_revoked_path(revline[0]))
        self._revlog.log_info(
            tegevus='ennistamine',
            isikukood=revline[0],
            nimi=revline[1],
            timestamp=timest,
            operaator=operator,
            pohjus=revline[2])

    def revoke_vote(self, revline, operator):
        timest = self.get_latest_vote(revline[0])
        nowstr = time.strftime("%Y%m%d%H%M%S", time.localtime())
        self._reg.create_string_value(
            htscommon.get_user_key(revline[0]), 'reason',
            "%s\t%s" % (nowstr, revline[2]))

        self._revlog.log_info(
            tegevus='tühistamine',
            testtime=nowstr,
            isikukood=revline[0],
            nimi=revline[1],
            timestamp=timest,
            operaator=operator,
            pohjus=revline[2])

    def is_user_revoked(self, pc):
        user_key = htscommon.get_user_key(pc)
        if self._reg.check(user_key + ['reason']):
            line = self._reg.read_string_value(user_key, 'reason').value
            data = line.split('\t')
            return True, data[1], data[0]
        return False, '', ''

    def save_log(self, lines, log):
        fn = self._reg.path(['common', 'log%s' % log])
        lf = htscommon.LoggedFile(fn)
        lf.open('w')
        lf.write(evcommon.VERSION + "\n")
        lf.write(self._elid + "\n")
        lf.write("%s\n" % log)
        for el in lines:
            lf.write(el + '\n')
        lf.close()

    def save_revocation_report(self, report):
        fn = self._reg.path(['hts', 'output', evcommon.REVREPORT_FILE])
        outfile = htscommon.LoggedFile(fn)
        outfile.open('a')
        for el in report:
            outfile.write("\t".join(el) + "\n")

        outfile.close()

    def talletaja(self, ik):
        vl = None
        try:
            vl = inputlists.VotersList('hts', self._reg)
            if not vl.has_voter(ik):
                return None
            ret = vl.get_voter(ik)
            return ret
        finally:
            if vl is not None:
                vl.close()
                vl = None


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
