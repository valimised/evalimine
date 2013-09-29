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
import os

import evcommon
import evmessage
import evstrings
import htsalldisp
import protocol
import sessionid
from evlog import AppLog

def bad_parameters():
    protocol.http_response(evcommon.VERSION + "\n" + \
            evcommon.VERIFY_ERROR + "\n" + \
            evmessage.EvMessage().get_str("BAD_PARAMETERS", \
                evstrings.BAD_PARAMETERS))
    cgi.sys.exit(0)

if not evcommon.testrun():

    os.umask(007)

    APP = "hts-verify-vote.cgi"
    AppLog().set_app(APP)

    form = cgi.FieldStorage()

    vote = None

    if form.has_key(evcommon.POST_SESS_ID):
        sessionid.setsid(form.getvalue(evcommon.POST_SESS_ID))

    if form.has_key(evcommon.POST_VERIFY_VOTE):
        values = form.getlist(evcommon.POST_VERIFY_VOTE)
        if len(values) == 1:
            vote = values[0]
        else:
            # Don't write the values to disk; we don't know how large they are
            AppLog().log_error("Too many parameter values")
            bad_parameters()

    protocol.http_response(htsalldisp.verify_vote(vote))
    cgi.sys.exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
