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

import purge
from election import Election
from election import ElectionState
import evcommon


def purge_sessions(spool_key, description):

    # Read the session length value before defining check_session, so we only
    # have to read it once.
    length = Election().get_session_length() * 60

    def check_session(reg, session_id, runtime):
        start = reg.read_integer_value([spool_key, session_id], "start").value
        return start + length < runtime

    def purge_session(reg, session_id):
        reg.ensure_no_key([spool_key, session_id])

    purger = purge.Purger(description, [spool_key])
    purger.work(check_session, purge_session)


if __name__ == '__main__':
    if ElectionState().election_on():
        purge_sessions(evcommon.IDSPOOL, "expired ID-card session")
        purge_sessions(evcommon.MIDSPOOL, "expired Mobile-ID session")

# vim:set ts=4 sw=4 et fileencoding=utf8:
