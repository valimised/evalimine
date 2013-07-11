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

import cgi
import evcommon
import hesdisp
import protocol
import sessionid
import os

if not evcommon.testrun():
    os.umask(007)
    hesd = hesdisp.HESVoterDispatcher()
    form = cgi.FieldStorage()

    result = protocol.msg_error_technical()

    try:
        if form.has_key(evcommon.POST_EVOTE):
            if form.has_key(evcommon.POST_SESS_ID):
                sessionid.setsid(
                        form.getvalue(evcommon.POST_SESS_ID))
            result = hesd.hts_vote(form.getvalue(evcommon.POST_EVOTE))
        else:
            if not os.path.exists('/var/evote/registry/common/nonewvoters'):
                result = hesd.get_candidate_list()
            else:
                a, b = protocol.plain_error_election_off_after()
                result = protocol.msg_error(a, b)
    except:
        result = protocol.msg_error_technical()

    protocol.http_response(result)
    cgi.sys.exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
