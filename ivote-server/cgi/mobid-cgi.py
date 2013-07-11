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
import middisp
import protocol
import evlog
import sessionid
import os

if not evcommon.testrun():
    os.umask(007)
    form = cgi.FieldStorage()
    result = protocol.msg_error_technical()
    mid = middisp.MIDDispatcher()

    if form.has_key(evcommon.POST_SESS_ID):
        sessionid.setsid(form.getvalue(evcommon.POST_SESS_ID))
        if form.has_key(evcommon.POST_MID_POLL):
            result = mid.poll()
        else:
            result = mid.init_sign(form)
    else:
        if form.has_key(evcommon.POST_PHONENO):
            if not os.path.exists('/var/evote/registry/common/nonewvoters'):
                result = mid.init_auth(form.getvalue(evcommon.POST_PHONENO))
            else:
                a, b = protocol.plain_error_election_off_after()
                result = protocol.msg_error(a, b)
        else:
            evlog.log_error('Vigane POST päring: %s' % form.keys())

    protocol.http_response(result)
    cgi.sys.exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
