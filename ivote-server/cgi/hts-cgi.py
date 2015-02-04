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
    evlog.AppLog().set_app("HTS")

    try:
        if cgivalidator.validate_sessionid(form):
            sessionid.setsid(form.getvalue(evcommon.POST_SESS_ID))

        if evcommon.POST_EVOTE in form:
            # Store the vote
            req_params = [evcommon.POST_VOTERS_FILES_SHA256,
                          evcommon.POST_SESS_ID,
                          evcommon.POST_PERSONAL_CODE,
                          evcommon.POST_EVOTE]
            res, logline = cgivalidator.validate_form(form, req_params)
            if res:
                sha = form.getvalue(evcommon.POST_VOTERS_FILES_SHA256)
                code = form.getvalue(evcommon.POST_PERSONAL_CODE)
                vote = form.getvalue(evcommon.POST_EVOTE)
                result = htsalldisp.store_vote(sha, code, vote)
            else:
                evlog.log_error("vote/err, " + logline)

        elif (evcommon.POST_SESS_ID in form
                or evcommon.POST_PERSONAL_CODE in form):
            # Check for repeat voting
            req_params = [evcommon.POST_VOTERS_FILES_SHA256,
                          evcommon.POST_SESS_ID,
                          evcommon.POST_PERSONAL_CODE]
            res, logline = cgivalidator.validate_form(form, req_params)
            if res:
                sha = form.getvalue(evcommon.POST_VOTERS_FILES_SHA256)
                code = form.getvalue(evcommon.POST_PERSONAL_CODE)
                result = htsalldisp.check_repeat(sha, code)
            else:
                evlog.log_error("repeat/err, " + logline)

        else:
            # Check consistency
            req_params = [evcommon.POST_VOTERS_FILES_SHA256]
            res, logline = cgivalidator.validate_form(form, req_params)
            if res:
                sha = form.getvalue(evcommon.POST_VOTERS_FILES_SHA256)
                result = htsalldisp.consistency(sha)
            else:
                evlog.log_error("consistency/err, " + logline)
    except:
        evlog.log_exception()
        result = protocol.msg_error_technical()

    protocol.http_response(result)
    cgi.sys.exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
