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

import sys
import shutil
import ConfigParser
import evreg
import evcommon

import singleton

MSG_FILE = ['common', 'teated']

# Selle klassi ainus mõte on, et EV_ERRORS. abil saab lähtekoodis markeerida
# veakoode - siis on vajadusel mugav greppida neid.


class EvErrors:

    def __getattr__(self, attr):
        return attr

EV_ERRORS = EvErrors()


class EvMessage:

    """Message strings handling class, Singleton pattern
    """

    __metaclass__ = singleton.SingletonType

    def __init__(self):
        # Siin hoitakse mäppuvana koodid ja stringid.
        self.msg_strings = {}
        evreg.create_registry(evcommon.EVREG_CONFIG)
        self.reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
        try:
            self._load_strings()
        except:
            pass

    def _load_strings(self):
        if self.reg.check(MSG_FILE):
            fn = self.reg.path(MSG_FILE)
            config = ConfigParser.ConfigParser()
            config.readfp(open(fn, 'r'))
            for i in config.sections():
                for j in config.options(i):
                    self.msg_strings[j] = config.get(i, j)

    def import_str_file(self, file_name):
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(open(file_name, 'r'))
            shutil.copyfile(file_name, self.reg.path(MSG_FILE))
            self._load_strings()
        except: # pylint: disable=W0702
            exctype, value = sys.exc_info()[:2]
            print('Teadete laadimine ei õnnestunud: %s: \"%s\"' %
                  (exctype, value))
            return
        print 'Teadete laadimine oli edukas.'

    def get_str(self, key, default_msg):
        k = key.lower()
        if k in self.msg_strings:
            return self.msg_strings[k]
        return default_msg

    def print_all_strings(self):
        pairs = zip(self.msg_strings.keys(), self.msg_strings.values())
        print "USER STRINGS:\n"
        for j in pairs:
            print j

if __name__ == '__main__':
    EvMessage().print_all_strings()

# vim:set ts=4 sw=4 et fileencoding=utf8:
