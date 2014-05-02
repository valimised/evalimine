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
import formatutil
import inputlists

class RevocationList(inputlists.InputList):

    def __init__(self):
        inputlists.InputList.__init__(self)
        self.name = 'Tühistus/ennistus'
        self.revoke = False
        self.rev_list = []
        self.__uniq = {}

    def checkuniq(self, line):
        lst = line.split('\t')
        key = lst[0]
        if key in self.__uniq:
            self.errcons('Mitmekordne tühistamine/ennistamine')
            return False
        self.__uniq[key] = '.'
        self.rev_list.append(lst)
        return True

    def dataline(self, line):
        lst = line.split('\t')
        if not len(lst) == 3:
            self.errform('Kirjete arv real')
            return False

        if not formatutil.is_isikukood(lst[0]):
            self.errform('Vigase vorminguga isikukood')
            return False

        if not formatutil.is_nimi(lst[1]):
            self.errform('Nimi')
            return False

        if not formatutil.is_pohjus(lst[2]):
            self.errform('Põhjus')
            return False

        return True

    def my_header(self, infile):
        data = self.current(infile.readline())
        if data == 'tühistus':
            self.revoke = True
        elif data == 'ennistus':
            self.revoke = False
        else:
            self.errform('Faili tüüp')
            return False
        return True


def main_function():
    rl = RevocationList()
    if not rl.check_format(sys.argv[1]):
        print "Nimekiri ei vasta formaadinõuetele"
        sys.exit(1)

    if rl.revoke:
        print 'Tegu on tühistusnimekirjaga'
    else:
        print 'Tegu on ennistusnimekirjaga'

    for el in rl.rev_list:
        print el

    print "Nimekiri OK"


if __name__ == '__main__':
    main_function()


# vim:set ts=4 sw=4 et fileencoding=utf8:
