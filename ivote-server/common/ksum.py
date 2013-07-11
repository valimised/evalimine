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

import hashlib
import base64
import os
import sys


def filename(data_file):
    ext = ".sha1"
    return data_file + ext


def _has(ffile):
    return os.access(ffile, os.F_OK)


def _check_file(ffile):
    if not _has(ffile):
        raise Exception("Faili " + ffile + " ei eksisteeri")


def _read_sha1(ffile):
    _check_file(ffile)
    _rf = open(ffile, "r")
    try:
        return base64.decodestring(_rf.read())
    finally:
        _rf.close()


def has(data_file):
    return _has(filename(data_file))


def compute_voters_files_sha1(voters_file_hashes_dir):
    file_list = os.listdir(voters_file_hashes_dir)
    file_list.sort()
    _s = hashlib.sha1()
    for i in file_list:
        _s.update(i)
    return _s.hexdigest()


def compute(ffile):
    _check_file(ffile)
    _rf = open(ffile, "r")
    try:
        _s = hashlib.sha1()
        for line in _rf:
            _s.update(line)
        return _s.hexdigest()
    finally:
        _rf.close()


def store(data_file):
    checksum = compute(data_file)
    ksum_f = file(filename(data_file), "w")
    try:
        ksum_f.write(base64.encodestring(checksum))
    finally:
        ksum_f.close()


def check(data_file):
    try:
        checksum = _read_sha1(filename(data_file))
        checksum2 = compute(data_file)
        return checksum == checksum2
    except: # pylint: disable=W0702
        return False


def votehash(vote):
    return base64.encodestring(hashlib.sha1(vote).digest()).strip()


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
