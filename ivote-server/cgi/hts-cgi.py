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

import htsalldisp
import cgi
import evcommon
import protocol
import sessionid
import os

def bad_input():
    _msg = htsalldisp.bad_cgi_input()
    protocol.http_response(_msg)
    cgi.sys.exit(0)


if not evcommon.testrun():
    os.umask(007)
    form = cgi.FieldStorage()

    has_sha1 = form.has_key(evcommon.POST_VOTERS_FILES_SHA1)
    has_code = form.has_key(evcommon.POST_PERSONAL_CODE)
    has_vote = form.has_key(evcommon.POST_EVOTE)
    has_sess = form.has_key(evcommon.POST_SESS_ID)

    if (not has_sha1):
        bad_input()

    val_sha = form.getvalue(evcommon.POST_VOTERS_FILES_SHA1)

    if (not has_code) and (not has_vote):
        msg = htsalldisp.consistency(val_sha)
        protocol.http_response(msg)
        cgi.sys.exit(0)

    if (has_sess):
        sessionid.setsid(form.getvalue(evcommon.POST_SESS_ID))

    if has_code and has_vote:
        if (has_sess):
            val_code = form.getvalue(evcommon.POST_PERSONAL_CODE)
            val_vote = form.getvalue(evcommon.POST_EVOTE)
            msg = htsalldisp.store_vote(val_sha, val_code, val_vote)
            protocol.http_response(msg)
            cgi.sys.exit(0)
        else:
            bad_input()

    if has_code and (not has_vote):
        if (has_sess):
            val_code = form.getvalue(evcommon.POST_PERSONAL_CODE)
            msg = htsalldisp.check_repeat(val_sha, val_code)
            protocol.http_response(msg)
            cgi.sys.exit(0)
        else:
            bad_input()

    bad_input()


# vim:set ts=4 sw=4 et fileencoding=utf8:
