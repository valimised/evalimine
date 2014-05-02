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

import evcommon
from evmessage import EV_ERRORS

def http_response(content):
    print 'Content-Type: text/plain'
    print 'Content-Length: %d' % (len(content) + 1)
    print
    print content

def msg_ok(msg):
    return evcommon.VERSION + '\n' + evcommon.EVOTE_OK + '\n' + msg


def msg_repeat(cand, repeat):
    return msg_ok(cand + "\nkorduv\t" + repeat)


def msg_error(errcode, msg):
    return evcommon.VERSION + '\n' + errcode + '\n' + msg


def msg_error_technical():
    p1, p2 = plain_error_technical(evcommon.EVOTE_ERROR)
    return msg_error(p1, p2)


def msg_mobid_auth_init_ok(sesscode, challenge):
    return msg_ok(sesscode + '\t' + challenge)

def msg_mobid_sign_init_ok(challenge):
    return msg_ok(challenge)

def msg_mobid_poll():
    return msg_error(evcommon.EVOTE_POLL, '')


def plain_error_technical(code):
    return code, EV_ERRORS.TEHNILINE_VIGA


def plain_error_maintainance():
    return evcommon.EVOTE_ERROR, EV_ERRORS.HOOLDUS


def plain_error_election_off_before():
    return evcommon.EVOTE_ERROR, EV_ERRORS.HAALETUS_POLE_ALANUD


def plain_error_election_off_after():
    return evcommon.EVOTE_ERROR, EV_ERRORS.HAALETUS_ON_LOPPENUD

# vim:set ts=4 sw=4 et fileencoding=utf8:
