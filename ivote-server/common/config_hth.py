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
from election import Election


def usage():
    print 'Kasutamine: ' + sys.argv[0] + ' <hts> <htspath> <htsverifypath>'
    sys.exit(1)


def execute(ip, path, verify):
    Election().set_hts_ip(ip)
    Election().set_hts_path(path)
    Election().set_hts_verify_path(verify)
    Election().config_hth_done()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        usage()

    try:
        execute(*sys.argv[1:])
    except:
        Election().config_hth_done(False)
        sys.stderr.write("HTSi konfigureerimine nurjus: %s\n"
            % exception_msg.trace())
        sys.exit(1)


# vim:set ts=4 sw=4 et fileencoding=utf8:
