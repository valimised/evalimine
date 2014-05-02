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

import hashlib
import base64
import os
import sys


SHA256 = "sha256"
SHA1 = "sha1"


def filename(data_file, ext):
    return data_file + ext


def _has(ffile):
    return os.access(ffile, os.F_OK)


def _check_file(ffile):
    if not _has(ffile):
        raise Exception("Faili " + ffile + " ei eksisteeri")


def _read_sha256(ffile):
    _check_file(ffile)
    _rf = open(ffile, "r")
    try:
        return _rf.read()
    finally:
        _rf.close()


def compute_voters_files_sha256(voters_file_hashes_dir):
    file_list = os.listdir(voters_file_hashes_dir)
    file_list.sort()
    _s = hashlib.sha256()
    for i in file_list:
        _s.update(i)
    return _s.hexdigest()


def compute(ffile):
    _check_file(ffile)
    _rf = open(ffile, "r")
    try:
        _s = hashlib.sha256()
        for line in _rf:
            _s.update(line)
        return _s.hexdigest()
    finally:
        _rf.close()

def compute_sha1(ffile):
    with open(ffile, "r") as f:
        return base64.encodestring(hashlib.sha1(f.read()).hexdigest()).strip()
    return None


def store(data_file):
    checksum = compute(data_file)
    ksum_f = file("%s.%s" % (data_file, SHA256), "w")
    try:
        ksum_f.write(checksum)
    finally:
        ksum_f.close()


def check(data_file, strict = False):

    checksum_now = compute(data_file)
    checksum_file = None
    method = None

    fn = "%s.%s" % (data_file, SHA256)
    if _has(fn):
        with open(fn, "r") as f:
            checksum_file = f.read()
            method = SHA256

    fn = "%s.%s" % (data_file, SHA1)
    if (checksum_file == None) and _has(fn):
        with open(fn, "r") as f:
            checksum_file = f.read().strip()
            method = SHA1
            checksum_now = compute_sha1(data_file)

    if checksum_file:
        print "Kontrollsummafail olemas, kontrollin (%s)." % method
        return (checksum_now == checksum_file)

    if strict:
        return False

    print "Kontrollsummafail puudub, kuvan kontrollsumma (%s)." % SHA256
    print checksum_now
    return True


def votehash(vote):
    return base64.encodestring(hashlib.sha256(vote).digest()).strip()


def usage():
    print "Kasutamine:"
    print "    %s <store|check> <data_file>" % sys.argv[0]
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
    if sys.argv[1] != "store" and sys.argv[1] != "check":
        usage()

    if sys.argv[1] == "store":
        store(sys.argv[2])
    else:
        if not check(sys.argv[2]):
            print "Kontrollsumma ei klapi"
        else:
            print "Kontrollsumma klapib"

# vim:set ts=4 sw=4 et fileencoding=utf8:
