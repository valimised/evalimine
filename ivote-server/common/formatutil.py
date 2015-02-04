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

import re

RE_ELID = re.compile('^\w{1,28}$')
RE_ISIKUKOOD = re.compile('^\d\d\d\d\d\d\d\d\d\d\d$')
RE_100UTF8 = re.compile('^.{1,100}$', re.UNICODE)
RE_200UTF8 = re.compile('^.{1,200}$', re.UNICODE)
RE_100UTF8OPT = re.compile('^.{0,100}$', re.UNICODE)
RE_VERSIOON = re.compile('^\d{1,2}$')
RE_VALIK = re.compile('^\d{1,10}\.\d{1,11}$')
RE_NUMBER10 = re.compile(r'^\d{1,10}$')
RE_BASE64 = re.compile('^[a-zA-Z0-9+/=]+$')
RE_BASE64_LINES = re.compile('^[a-zA-Z0-9+/=\n]+$')
RE_HEX = re.compile('^[a-fA-F0-9]+$')
RE_LINENO = re.compile('^\d{0,11}$')
RE_PHONENO = re.compile(r'^\+(\d){7,15}$')
RE_SIGNING_TIME = re.compile('^[TZ0-9:-]+$')
RE_NUMBER100 = re.compile('^\d{1,100}$')

MAX_VOTE_BASE64_SIZE = 24000


# pylint: disable=C0103
def is_jaoskonna_number_kov_koodiga(p1, p2):
    if not is_jaoskonna_omavalitsuse_kood(p1):
        return False
    if not is_jaoskonna_number_kov_sees(p2):
        return False
    return True


def is_ringkonna_number_kov_koodiga(p1, p2):
    if not is_ringkonna_omavalitsuse_kood(p1):
        return False
    if not is_ringkonna_number_kov_sees(p2):
        return False
    return True


def is_jaoskonna_number_kov_sees(nr):
    return is_jaoskonna_number(nr)


def is_jaoskonna_omavalitsuse_kood(nr):
    return is_omavalitsuse_kood(nr)


def is_ringkonna_number_kov_sees(nr):
    return is_ringkonna_number(nr)


def is_ringkonna_omavalitsuse_kood(nr):
    return is_omavalitsuse_kood(nr)


def is_omavalitsuse_kood(nr):
    return _is_number10(nr)


def is_valimiste_identifikaator(elid):
    return RE_ELID.match(elid) is not None


def is_isikukood(code):
    return RE_ISIKUKOOD.match(code) is not None


def is_ringkonna_number(nr):
    return _is_number10(nr)


def is_jaoskonna_number(nr):
    return _is_number10(nr)


def is_100utf8(sstr):
    return RE_100UTF8.match(sstr) is not None


def is_200utf8(sstr):
    return RE_200UTF8.match(sstr) is not None


def is_100utf8optional(sstr):
    return RE_100UTF8OPT.match(sstr) is not None


def is_ringkonna_nimi(name):
    return is_100utf8(name)


def is_maakonna_nimi(name):
    return is_100utf8(name)


def is_jaoskonna_nimi(name):
    if not is_100utf8(name):
        return False

    parts = name.split(',')
    record_type = len(parts)
    if not (record_type in [2, 3, 4, 5]):
        return False
    return True


def is_versiooninumber(nr):
    return RE_VERSIOON.match(nr) is not None


def is_nimi(name):
    return is_100utf8(name)


def is_pohjus(sstr):
    return is_100utf8(sstr)


def is_valiku_kood(code):
    return RE_VALIK.match(code) is not None


def is_valiku_nimi(name):
    return is_100utf8(name)


def is_valimisnimekirja_nimi(name):
    return is_100utf8optional(name)


def is_rea_number_voi_tyhi(nr):
    return RE_LINENO.match(nr) is not None


def is_number100(nr):
    return RE_NUMBER100.match(nr) is not None


def _is_number10(nr):
    return RE_NUMBER10.match(nr) is not None


def is_signing_time(str_):
    return RE_SIGNING_TIME.match(str_) is not None


def is_base64(str_):
    return RE_BASE64.match(str_) is not None


def is_base64_lines(str_):
    return RE_BASE64_LINES.match(str_) is not None


def is_vote(str_):
    return (len(str_) < MAX_VOTE_BASE64_SIZE) and \
        (RE_BASE64_LINES.match(str_) is not None)


def is_mobid_poll(str_):
    return is_mobid_poll_auth(str_) or is_mobid_poll_vote(str_)


def is_mobid_poll_auth(str_):
    return str_ == "auth"


def is_mobid_poll_vote(str_):
    return str_ == "vote"


def is_mobid_phoneno(str_):
    return RE_PHONENO.match(str_) is not None


def is_voters_file_sha256(str_):
    return len(str_) == 64 and is_hex(str_)


def is_session_id(str_):
    return len(str_) == 20 and is_hex(str_)


def is_vote_verification_id(str_):
    return len(str_) == 40 and is_hex(str_)


def is_hex(str_):
    return RE_HEX.match(str_) is not None

# vim:set ts=4 sw=4 et fileencoding=utf8:
