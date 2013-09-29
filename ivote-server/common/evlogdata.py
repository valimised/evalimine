# log
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
import M2Crypto
import hashlib
import urllib
import exception_msg

def get_apache_env(key):
    if os.environ.has_key(key):
        return os.environ[key]
    return ''

def get_remote_ip():
    return get_apache_env('REMOTE_ADDR')

def get_user_agent():
    return urllib.quote_plus(get_apache_env('HTTP_USER_AGENT'))[:100]


def get_vote(name, data):
    return "VOTE=%s, SHA1=%s" % \
            (name, hashlib.sha1(data).digest().encode('hex'))


def get_cert_data_log(cert_pem, prefix = None, addlines = False):

    retval = ''

    isik = 'N/A'
    serial = 'N/A'
    certhash = 'N/A'
    org = 'N/A'
    exc = None

    my_cert_pem = cert_pem
    if addlines:
        bline = '-----BEGIN CERTIFICATE-----\n'
        eline = '\n-----END CERTIFICATE-----'
        my_cert_pem = bline + my_cert_pem + eline

    try:
        cert = M2Crypto.X509.load_cert_string(my_cert_pem)
        isik = cert.get_subject().serialNumber
        serial = cert.get_serial_number()
        certhash = hashlib.sha256(cert.as_der()).digest().encode('hex')
        org = cert.get_subject().O
    except:
        exc = exception_msg.trace()

    retval = "PC=%s, SERIAL=%s, HASH=%s, ORG=%s" % \
            (isik, serial, certhash, org)

    if exc:
        retval = retval + ", error occured"

    if prefix:
        retval = prefix + " " + retval

    return retval, exc

# vim:set ts=4 sw=4 et fileencoding=utf8:
