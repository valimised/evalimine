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

import os
import evcommon
import evlog
import evlogdata

def get_loglines(prefix):
    to_alog = []
    to_elog = []

    to_alog.append(prefix + " REMOTE_ADDR: " + evlogdata.get_remote_ip())
    to_alog.append(prefix + " HTTP_USER_AGENT: " + evlogdata.get_user_agent())

    if evcommon.HTTP_CERT in os.environ:
        cert = os.environ[evcommon.HTTP_CERT]
        if len(cert) > 0:
            alog, elog = evlogdata.get_cert_data_log(cert, prefix)
            to_alog.append(alog)
            if elog:
                to_elog.append(elog)

    return to_alog, to_elog

def do_log(prefix):
    alog, elog = get_loglines(prefix)
    for el in alog:
        evlog.log(el)
    for el in elog:
        evlog.log_error(el)

def do_log_error(prefix):
    alog, elog = get_loglines(prefix)
    for el in alog:
        evlog.log_error(el)
    for el in elog:
        evlog.log_error(el)

# vim:set ts=4 sw=4 et fileencoding=utf8:
