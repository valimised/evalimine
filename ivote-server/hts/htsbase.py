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

import evlog
import htscommon
import evcommon
from election import Election


class HTSBase:

    def __init__(self, elid):
        self._elid = elid
        self._errmsg = None
        self._reg = Election().get_sub_reg(self._elid)

        self._log1 = evlog.Logger()
        self._log1.set_format(evlog.EvLogFormat())
        self._log1.set_logs(self._reg.path(['common', 'log1']))

        self._log2 = evlog.Logger()
        self._log2.set_format(evlog.EvLogFormat())
        self._log2.set_logs(self._reg.path(['common', 'log2']))

        self._log3 = evlog.Logger()
        self._log3.set_format(evlog.EvLogFormat())
        self._log3.set_logs(self._reg.path(['common', 'log3']))

        self._revlog = evlog.Logger()
        self._revlog.set_format(evlog.RevLogFormat())
        self._revlog.set_logs(self._reg.path(['common', evcommon.REVLOG_FILE]))

    def _haaletanud_konf(self, isikukood):
        user_key = htscommon.get_user_key(isikukood)
        return self._reg.check(user_key) and \
                len(self._reg.list_keys(user_key)) > 0

    def haaletanud(self, isikukood):
        logi = self._log1.contains(isikukood)
        konf = self._haaletanud_konf(isikukood)
        if logi and konf:
            return True
        if (not logi) and (not konf):
            return False
        self._errmsg = 'Logifail LOG1 ja serveri olek ei ole kooskõlalised'
        raise Exception(self._errmsg)


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
