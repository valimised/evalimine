# Session identification
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
import singleton

APACHE_UNIQUE_ID = "UNIQUE_ID"
COMMAND_LINE = "cmd"


class InternalSessionID:

    __metaclass__ = singleton.SingletonType

    __apache_id = None
    __session_id = None

    def __init__(self):
        self.reset()

    def reset(self):
        self.__apache_id = os.environ.get(APACHE_UNIQUE_ID)

        if not self.__apache_id:
            self.__apache_id = COMMAND_LINE

        self.__session_id = os.urandom(10).encode('hex')

    def setsid(self, uniq):
        if uniq:
            self.__session_id = uniq

    def voting(self):
        return self.__session_id

    def apache(self):
        return self.__apache_id


def apache():
    return InternalSessionID().apache()


def voting():
    return InternalSessionID().voting()


def setsid(sid):
    InternalSessionID().setsid(sid)


def reset():
    InternalSessionID().reset()


# vim:set ts=4 sw=4 et fileencoding=utf8:
