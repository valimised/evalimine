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

import fcntl
import base64
import re

REVOKE_REASON_PATTERN = re.compile('^reason$')
VALID_VOTE_PATTERN = re.compile('^valid_.*_.*$', re.DOTALL)
AUTOREVOKED_VOTE_PATTERN = re.compile('^autorevoked_.*_.*$', re.DOTALL)
USERREVOKED_VOTE_PATTERN = re.compile('^userrevoked_.*_.*$', re.DOTALL)
VOTE_VERIFICATION_ID_FILENAME = "otp"

BVALID = 1
BUSERREVOKED = 2
BAUTOREVOKED = 3

def get_verification_key(otp=None):
    key = ['verification', 'otps']
    if otp:
        key.append(otp)
    return key

def get_user_key(code):
    return ['hts', 'votes', code[7:11], code]


def join_voter(voter):
    return '\t'.join([
        voter['nimi'],
        voter['ringkond_omavalitsus'],
        voter['ringkond'],
        voter['jaoskond_omavalitsus'],
        voter['jaoskond'],
        voter['reanumber']])


def get_votefile_voter(filename):
    llist = filename.split('_')
    voter = base64.b64decode(llist[2], "+-").split('\t')
    ret = {
            'nimi': voter[0],
            'jaoskond_omavalitsus': voter[3],
            'jaoskond': voter[4],
            'ringkond_omavalitsus': voter[1],
            'ringkond': voter[2],
            'reanumber': voter[5]}
    return ret


def get_votefile_time(filename):
    llist = filename.split('_')
    return llist[1]


def b64_voter(voter):
    return base64.b64encode(join_voter(voter), "+-").strip()


def valid_votefile_name(timestamp, voter):
    return '_'.join(['valid', timestamp, b64_voter(voter)])


def change_votefile_name(old_name, rtype):
    llist = old_name.split('_')
    if (rtype == BAUTOREVOKED):
        llist[0] = 'autorevoked'
    elif (rtype == BUSERREVOKED):
        llist[0] = 'userrevoked'
    else:
        llist[0] = 'valid'
    return '_'.join(llist)


class VoteCounter:

    def __init__(self):
        self.__v_votes = 0
        self.__a_votes = 0
        self.__r_votes = 0
        self.__n_votes = 0

    def valid(self):
        return self.__v_votes

    def inc_valid(self):
        self.__v_votes += 1

    def userrevoked(self):
        return self.__r_votes

    def inc_userrevoked(self):
        self.__r_votes += 1

    def autorevoked(self):
        return self.__a_votes

    def inc_autorevoked(self):
        self.__a_votes += 1

    def unknown(self):
        return self.__n_votes

    def inc_unknown(self):
        self.__n_votes += 1


class LoggedFile:

    def __init__(self, filen, logger):
        self.__filename = filen
        self.__file = None
        self.__logger = logger

    def name(self):
        return self.__filename

    def open(self, mode):
        try:
            self.__file = file(self.__filename, mode)
            fcntl.lockf(self.__file, fcntl.LOCK_EX)
        except Exception, (errno, errstr):
            self.__logger.log_error("Faili '%s' avamine moodis '%s' nurjus" % \
                (self.__filename, mode))
            raise Exception(errno, errstr)

    def write(self, writestr):
        self.__file.write(writestr)

    def close(self):
        try:
            self.__file.close()
        except Exception, (errno, errstr):
            self.__logger.log_error(\
                "Faili '%s' sulgemine nurjus" % self.__filename)
            raise Exception(errno, errstr)


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
