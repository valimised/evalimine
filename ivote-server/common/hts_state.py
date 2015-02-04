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
import exception_msg
import election
import htsdisp


def execute():
    _state = election.ElectionState().get()
    if _state == election.ETAPP_TYHISTUS:
        qlist = election.Election().get_questions()
        for el in qlist:
            print el
            htsdisp.start_revocation(el)
    elif _state == election.ETAPP_LUGEMINE:
        qlist = election.Election().get_questions()
        for el in qlist:
            print el
            htsdisp.start_tabulation(el)
    else:
        pass


def usage():
    sys.stderr.write('Kasutamine: %s\n' % sys.argv[0])
    sys.exit(1)


if __name__ == '__main__':

    if len(sys.argv) != 1:
        usage()

    try:
        execute()
    except: # pylint: disable=W0702
        sys.stderr.write(
            'Viga etapivahetusel: ' + exception_msg.trace() + '\n')
        sys.exit(1)

# vim:set ts=4 sw=4 et fileencoding=utf8:
