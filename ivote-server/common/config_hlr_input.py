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

import shutil
import sys
import ksum
from election import Election


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

    if not ksum.check(_if, True):
        print "Kontrollsumma ei klapi"
        sys.exit(1)

    reg = Election().get_sub_reg(el_id)
    reg.ensure_key(['hlr', 'input'])
    dst = reg.path(['hlr', 'input', 'votes'])
    shutil.copy(_if, dst)
    ksum.store(dst)
    Election().config_hlr_input_elid_done(el_id)


if __name__ == '__main__':
    main_function()


# vim:set ts=4 sw=4 et fileencoding=utf8:
