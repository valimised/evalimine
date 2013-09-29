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
import urllib

import evcommon
import evmessage
import evstrings
import election
import formatutil
import protocol
import evlog
import evlogdata
import sessionid

os.umask(007)

APP = "hes-verify-vote.cgi"


def bad_parameters():
    protocol.http_response(evcommon.VERSION + "\n" + \
            evcommon.VERIFY_ERROR + "\n" + \
            evmessage.EvMessage().get_str("BAD_PARAMETERS", \
                evstrings.BAD_PARAMETERS))
    cgi.sys.exit(0)

if not evcommon.testrun():
    elec = election.Election()
    evlog.AppLog().set_app(APP)

    # Create a list of pairs from the form parameters. Don't use a dictionary
    # because that will overwrite recurring keys.
    form = cgi.FieldStorage()
    params = []
    for key in form:
        for value in form.getlist(key):
            params.append((key, value))

    # Only accept up to a single parameter
    if len(params) > 1:
        def keys(pairs):
            """Return a comma-separated list of the keys."""
            return ", ".join([pair[0] for pair in pairs])

        evlog.log_error("Too many query parameters: " + keys(params))
        bad_parameters()

    # Only accept the POST_VERIFY_VOTE parameter.
    if len(params) and params[0][0] != evcommon.POST_VERIFY_VOTE:
        evlog.log_error("Unknown query parameter \"%s\"" % params[0][0])
        bad_parameters()

    # Make sure the parameter is correctly formatted.
    if not formatutil.is_vote_verification_id(params[0][1]):
        # Don't write to disk; we don't know how large the value is
        evlog.log_error("Malformed vote ID")
        bad_parameters()

    evlog.log("verif/auth REMOTE_ADDR: " + evlogdata.get_remote_ip())
    evlog.log("verif/auth VOTE-ID: " + params[0][1])

    params.append((evcommon.POST_SESS_ID, sessionid.voting()))

    url = "http://" + elec.get_hts_ip() + "/" + elec.get_hts_verify_path()
    conn = urllib.urlopen(url, urllib.urlencode(params))
    protocol.http_response(conn.read())
    cgi.sys.exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
