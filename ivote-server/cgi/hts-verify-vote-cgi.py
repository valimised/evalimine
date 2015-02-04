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

import cgi
import evcommon
import evlog
import protocol
import sessionid
import cgivalidator
import htsalldisp
import os

if not evcommon.testrun():
    os.umask(007)
    form = cgi.FieldStorage()
    result = protocol.msg_error_technical()
    evlog.AppLog().set_app("VERIFY")

    try:
        if cgivalidator.validate_sessionid(form):
            sessionid.setsid(form.getvalue(evcommon.POST_SESS_ID))

        req_params = [evcommon.POST_SESS_ID, evcommon.POST_VERIFY_VOTE]
        res, logline = cgivalidator.validate_form(form, req_params)
        if res:
            vote = form.getvalue(evcommon.POST_VERIFY_VOTE)
            result = htsalldisp.verify_vote(vote)
        else:
            evlog.log_error(logline)
    except:
        evlog.log_exception()
        result = protocol.msg_error_technical()

    protocol.http_response(result)
    cgi.sys.exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
