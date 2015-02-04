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
import election
import evcommon
import exception_msg

G_HES_KEYS = ['hes', 'hes/voters']
G_HTS_KEYS = ['hts', 'hts/output', 'hts/voters']
G_HLR_KEYS = ['hlr', 'hlr/input', 'hlr/output']


class ElectionCreator:

    def __init__(self):
        self.__quest = None

    def init_hes(self):
        self.__quest.create_keys(G_HES_KEYS)

    def init_hts(self):
        import htscommon

        election.Election().get_root_reg().ensure_key(
                htscommon.get_verification_key())
        self.__quest.create_keys(G_HTS_KEYS)
        self.__quest.create_revlog()

    def init_hlr(self):
        self.__quest.create_keys(G_HLR_KEYS)

    def prepare(self, ex_elid, ex_type, ex_descr):
        election.create_registry()
        election.Election().init_keys()
        self.__quest = election.Election().new_question(
                ex_elid, ex_type, ex_descr)

    def init_done(self): # pylint: disable=R0201
        election.ElectionState().init()
        election.Election().init_conf_done()


def usage():
    print "Kasutamine:"
    print "    %s <hes|hts|hlr> <election id> <election type> <description>" \
        % sys.argv[0]
    print "        - Algväärtustab vastava serveri olekupuu"
    sys.exit(1)


def execute(ex_elid, ex_type, ex_descr):

    creat = ElectionCreator()

    creat.prepare(ex_elid, ex_type, ex_descr)

    if election.Election().is_hes():
        creat.init_hes()
    elif election.Election().is_hts():
        creat.init_hts()
    elif election.Election().is_hlr():
        creat.init_hlr()
    else:
        raise Exception('Serveri tüüp määramata')

    creat.init_done()
    print 'Lõpetasin töö edukalt'


def main_function():
    if not len(sys.argv) == 4:
        usage()

    if not int(sys.argv[2]) in evcommon.G_TYPES:
        usage()

    try:
        execute(sys.argv[1], sys.argv[2], sys.argv[3])
    except: # pylint: disable=W0702
        sys.stderr.write('Viga initsialiseerimisel: ' +
            exception_msg.trace() + '\n')
        sys.exit(1)


if __name__ == '__main__':
    main_function()


# vim:set ts=4 sw=4 et fileencoding=utf8:
