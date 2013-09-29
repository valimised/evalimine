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
import cgivalidator
import cgilog
import election
import os

if not evcommon.testrun():
    os.umask(007)
    form = cgi.FieldStorage()
    result = protocol.msg_error_technical()
    mid = middisp.MIDDispatcher()
    evlog.AppLog().set_app('MID')

    try:
        has_sess = form.has_key(evcommon.POST_SESS_ID)
        has_poll = form.has_key(evcommon.POST_MID_POLL)
        if has_sess:
            if cgivalidator.validate_sessionid(form):
                sessionid.setsid(form.getvalue(evcommon.POST_SESS_ID))
            if has_poll:
                req_params = [evcommon.POST_MID_POLL, evcommon.POST_SESS_ID]
                res, logline = cgivalidator.validate_form(form, req_params)
                if res:
                    result = mid.poll()
                else:
                    evlog.log_error(logline)
            else:
                req_params = [evcommon.POST_EVOTE, evcommon.POST_SESS_ID]
                res, logline = cgivalidator.validate_form(form, req_params)
                if res:
                    cgilog.do_log("vote/auth")
                    result = mid.init_sign(form)
                else:
                    cgilog.do_log_error('vote/auth/err')
                    evlog.log_error(logline)
        else:
            req_params = [evcommon.POST_PHONENO]
            res, logline = cgivalidator.validate_form(form, req_params)
            if res:
                cgilog.do_log("cand/auth")
                phoneno = form.getvalue(evcommon.POST_PHONENO)
                evlog.log("PHONENO: " + phoneno)
                if election.Election().allow_new_voters():
                    result = mid.init_auth(phoneno)
                else:
                    a, b = protocol.plain_error_election_off_after()
                    result = protocol.msg_error(a, b)
            else:
                cgilog.do_log_error('cand/auth/err')
                evlog.log_error(logline)
    except:
        evlog.log_exception()
        result = protocol.msg_error_technical()

    protocol.http_response(result)
    cgi.sys.exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
