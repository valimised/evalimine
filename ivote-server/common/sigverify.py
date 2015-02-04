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

import os
import base64
import sys
import binascii
from election import Election
import evcommon
import ksum

EXTENSIONS = [".signature", ".sig"]


def _has(ffile):
    return os.access(ffile, os.F_OK)


def check_sig_file(key_file):
    pubkey = open(key_file).read()
    parts = pubkey.split()

    if (" ".join(parts[0:3]) != "-----BEGIN PUBLIC KEY-----" or
            " ".join(parts[10:]) != "-----END PUBLIC KEY-----"):
        print "Võtmel puuduvad korrektsed päis ja jalus"
        return False
    try:
        base64.decodestring("".join(parts[3:10]))
    except:
        print "Võti ei läbinud base64 kodeeringu kontrolli"
        return False
    return True


def check_initial(data_file, key_file):
    with open(key_file, "r") as f:
        key = f.read()

    return check(data_file, key)


def check_existent(data_file, elid):
    key_path = Election().get_sub_reg(elid, ['common']).path()
    with open(key_path + evcommon.VOTER_PUBLIC_KEY, 'r') as f:
        key = f.read()

    return check(data_file, key)


def check(data_file, key):
    import bdocpython

    hexhash = ksum.compute(data_file)
    bhash = binascii.a2b_hex(hexhash)

    sig_file = None

    for ext in EXTENSIONS:
        tmp = "%s%s" % (data_file, ext)
        if _has(tmp):
            sig_file = tmp
            break

    if sig_file is None:
        return False, "Ei leia signatuuri faili: %s" % data_file

    with open(sig_file, "r") as f:
        sig = f.read()

    sv = bdocpython.SignatureVerifier()
    sv.setPubkey(key)
    sv.setSignature(sig)
    sv.setHash(bhash)

    res = sv.isSignatureOk()

    if not res:
        return False, sv.error

    return True, None


def usage():
    print "Kasutamine:"
    print "    %s <key_file> <data_file>" % sys.argv[0]
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
    check(sys.argv[1], sys.argv[2])


# vim:set ts=4 sw=4 et fileencoding=utf8:
