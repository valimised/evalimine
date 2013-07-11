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

import os
import sys
import ksum
from election import Election

def check_file(ffile):
    return os.access(ffile, os.F_OK)


def usage():
    print "Kasutamine:"
    print "    %s <valimiste_id> <loendamisele_minevate_häälte_fail>" \
        % sys.argv[0]
    sys.exit(1)


def main_function():
    if len(sys.argv) != 3:
        usage()

    el_id = sys.argv[1]
    _if = sys.argv[2]

    if not check_file(_if):
        print "Faili " + _if + " ei eksisteeri"
        sys.exit(1)

    if not ksum.has(_if):
        print "Faili " + ksum.filename(_if) + " ei eksisteeri"
        sys.exit(1)

    if not ksum.check(_if):
        print "Kontrollsumma ei klapi"
        sys.exit(1)

    reg = Election().get_sub_reg(el_id)
    reg.ensure_key(['hlr', 'input'])
    dst = reg.path(['hlr', 'input', 'votes'])
    os.system("cp " + _if + " " + dst)
    os.system("cp " + ksum.filename(_if) + " " + ksum.filename(dst))
    Election().config_hlr_input_elid_done(el_id)


if __name__ == '__main__':
    main_function()


# vim:set ts=4 sw=4 et fileencoding=utf8:
