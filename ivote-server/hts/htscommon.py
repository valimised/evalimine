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

import fcntl
import re
import os

REVOKE_REASON_PATTERN = re.compile('^reason$')
VALID_VOTE_PATTERN = re.compile('^vote_.*_.*_.zip$', re.DOTALL)
PARTIAL_VOTE_PATTERN = re.compile('^vote_.*_.*_.zip.partial$', re.DOTALL)
VOTE_VERIFICATION_ID_FILENAME = "otp"

ZIP_BDOCFILE = "vote.bdoc"
ZIP_LOGFILE = "vote.log"

def get_verification_key(otp=None):
    key = ['verification', 'otps']
    if otp:
        key.append(otp)
    return key

def get_user_key(code):
    return ['hts', 'votes', code[7:11], code]

def get_votefile_time(filename):
    llist = filename.split('_')
    return llist[1]


def valid_votefile_name(timestamp):
    rnd = os.urandom(3).encode('hex')
    return '_'.join(['vote', timestamp, rnd,'.zip'])


def get_logline_voter(logline):
    voter = logline.split('\t')
    ret = {
        'timestamp': voter[0],
        'isikukood': voter[6],
        'nimi': '',
        'jaoskond_omavalitsus': voter[4],
        'jaoskond': voter[5],
        'ringkond_omavalitsus': voter[2],
        'ringkond': voter[3],
        'reanumber': ''}

    if len(voter) == 9:
        ret['nimi'] = voter[7]
        ret['reanumber'] = voter[8].rstrip()

    return ret


class LoggedFile:

    def __init__(self, filen):
        self.__filename = filen
        self.__file = None

    def name(self):
        return self.__filename

    def open(self, mode):
        self.__file = file(self.__filename, mode)
        fcntl.lockf(self.__file, fcntl.LOCK_EX)

    def write(self, writestr):
        self.__file.write(writestr)

    def close(self):
        self.__file.close()


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
